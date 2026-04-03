#include <stdio.h>
#include <string.h>
#include "queue.h"

/*
 * This program tests the producer-consumer queue by simulating
 * interleaved operations via a scripted sequence, demonstrating
 * the race condition bug without requiring actual threads.
 */

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <test_name>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "basic_push_pop") == 0) {
        /* Simple single-producer single-consumer, no interleaving */
        Queue q;
        queue_init(&q, 10);

        for (int i = 1; i <= 5; i++) {
            int ret = queue_push(&q, i * 10);
            if (ret != 0) {
                printf("FAIL: push %d failed\n", i);
                return 1;
            }
        }

        int ok = 1;
        for (int i = 1; i <= 5; i++) {
            int val;
            int ret = queue_pop(&q, &val);
            if (ret != 0) {
                printf("FAIL: pop %d returned %d\n", i, ret);
                ok = 0;
                break;
            }
            if (val != i * 10) {
                printf("FAIL: pop %d got %d expected %d\n", i, val, i * 10);
                ok = 0;
                break;
            }
        }
        if (ok) printf("PASS: basic_push_pop\n");

    } else if (strcmp(argv[1], "interleave_race") == 0) {
        /*
         * Simulate the race condition:
         * 1. Consumer A tries to pop from empty queue -> goes to WAITING
         * 2. Producer pushes item -> signals
         * 3. Consumer B pops successfully (takes the item) 
         * 4. Consumer A resumes after signal -> BUG: pops from empty queue!
         *
         * This sequence demonstrates the classic "if vs while" bug.
         */
        Queue q;
        queue_init(&q, 10);

        int val_a, val_b;
        int ret;

        /* Step 1: Consumer A tries to pop from empty queue */
        ret = queue_pop(&q, &val_a);
        if (ret != -2) {
            printf("FAIL: expected WAITING (-2) on empty pop, got %d\n", ret);
            return 1;
        }
        printf("STEP1: Consumer A waiting (queue empty)\n");

        /* Step 2: Producer pushes one item */
        queue_push(&q, 42);
        printf("STEP2: Producer pushed 42 (count=%d, signaled=%d)\n",
               q.count, q.signaled);

        /* Step 3: Consumer B pops the item first */
        ret = queue_pop(&q, &val_b);
        if (ret != 0) {
            printf("FAIL: Consumer B pop failed: %d\n", ret);
            return 1;
        }
        printf("STEP3: Consumer B popped %d (count=%d)\n", val_b, q.count);

        /* Step 4: Consumer A resumes after signal - BUG: queue is empty! */
        ret = queue_resume_pop(&q, &val_a);
        if (ret == -2) {
            /* Correct behavior: recognized queue is empty, went back to waiting */
            printf("STEP4: Consumer A correctly re-waited (queue empty)\n");
            printf("RESULT: NO_RACE\n");
        } else if (ret == 0) {
            /* Buggy: blindly dequeued from empty queue */
            printf("STEP4: Consumer A got %d from empty queue! count=%d\n",
                   val_a, q.count);
            if (q.count < 0) {
                printf("RESULT: RACE_DETECTED (count underflow: %d)\n", q.count);
            } else {
                printf("RESULT: RACE_DETECTED (garbage value from empty queue)\n");
            }
        } else {
            printf("STEP4: Unexpected return %d\n", ret);
            printf("RESULT: RACE_DETECTED\n");
        }

    } else if (strcmp(argv[1], "multi_interleave") == 0) {
        /*
         * More complex interleaving: multiple consumer-waits, each
         * getting spuriously signaled while another consumer steals the item.
         *
         * Sequence:
         * 1. Consumer A tries pop (empty) -> WAITING
         * 2. Consumer B tries pop (empty) -> WAITING
         * 3. Producer pushes item 1 -> signals
         * 4. Consumer A resumes (takes item 1) or gets garbage if bug
         * 5. Consumer B also resumes (BUG: queue is empty, pops garbage + underflows)
         * 6. Producer pushes item 2 -> signals
         * 7. Check final count consistency
         *
         * With the bug, consumer B's resume_pop underflows count to -1
         * and pops garbage, so the total is inconsistent.
         */
        Queue q;
        queue_init(&q, 10);

        int val_a = -1, val_b = -1;
        int total_valid_pops = 0;
        int sum_popped = 0;

        /* Step 1-2: Both consumers try to pop from empty queue */
        int ret_a = queue_pop(&q, &val_a);  /* returns -2 (WAITING) */
        /* Note: only one waiting_pop flag, so this is simplified.
           We manually track that both are waiting. */
        (void)ret_a;

        /* Step 3: Producer pushes 1 item */
        queue_push(&q, 100);

        /* Step 4: Consumer A resumes after signal */
        ret_a = queue_resume_pop(&q, &val_a);
        if (ret_a == 0) {
            total_valid_pops++;
            sum_popped += val_a;
        }

        /* Step 5: Consumer B also tries to resume (queue is now empty!) */
        /* Re-set the signal flag to simulate B also being woken */
        q.signaled = 1;
        q.waiting_pop = 1;
        int ret_b = queue_resume_pop(&q, &val_b);
        if (ret_b == 0) {
            total_valid_pops++;
            sum_popped += val_b;
        }

        /* Step 6: Push another item normally */
        queue_push(&q, 200);
        int val_c;
        int ret_c = queue_pop(&q, &val_c);
        if (ret_c == 0) {
            total_valid_pops++;
            sum_popped += val_c;
        }

        /* Expected: only 2 items pushed (100, 200), so only 2 valid pops.
         * Consumer B's resume should have returned -2, not 0. */
        printf("VALID_POPS: %d\n", total_valid_pops);
        printf("SUM: %d\n", sum_popped);
        printf("COUNT: %d\n", q.count);

        /* With correct code: 2 valid pops, sum=300, count=0 */
        /* With buggy code: 3 valid pops (B gets garbage), count goes negative */
        if (total_valid_pops == 2 && sum_popped == 300 && q.count >= 0) {
            printf("RESULT: CONSISTENT\n");
        } else {
            printf("RESULT: INCONSISTENT (pops=%d, sum=%d, count=%d)\n",
                   total_valid_pops, sum_popped, q.count);
        }

    } else if (strcmp(argv[1], "count_integrity") == 0) {
        /*
         * Test that count never goes negative.
         * With the bug, resume_pop on empty queue decrements count below 0.
         */
        Queue q;
        queue_init(&q, 5);

        int val;
        /* Pop from empty -> wait */
        queue_pop(&q, &val);
        /* Push one item -> signal */
        queue_push(&q, 99);
        /* Another consumer takes it */
        queue_pop(&q, &val);
        /* Resume the first consumer */
        queue_resume_pop(&q, &val);

        printf("COUNT: %d\n", q.count);
        if (q.count >= 0) {
            printf("RESULT: COUNT_OK\n");
        } else {
            printf("RESULT: COUNT_UNDERFLOW\n");
        }

    } else {
        printf("Unknown test: %s\n", argv[1]);
        return 1;
    }

    return 0;
}
