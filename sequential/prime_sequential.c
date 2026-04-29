#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static int is_prime(long long value)
{
    if (value < 2) {
        return 0;
    }
    if (value == 2) {
        return 1;
    }
    if (value % 2 == 0) {
        return 0;
    }

    for (long long divisor = 3; divisor * divisor <= value; divisor += 2) {
        if (value % divisor == 0) {
            return 0;
        }
    }

    return 1;
}

static double elapsed_seconds(struct timespec start, struct timespec end)
{
    return (double)(end.tv_sec - start.tv_sec) +
           (double)(end.tv_nsec - start.tv_nsec) / 1000000000.0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "Utilizare: %s <n>\n", argv[0]);
        return EXIT_FAILURE;
    }

    char *endptr = NULL;
    long long n = strtoll(argv[1], &endptr, 10);
    if (*endptr != '\0' || n < 2) {
        fprintf(stderr, "Eroare: n trebuie sa fie un numar intreg >= 2.\n");
        return EXIT_FAILURE;
    }

    struct timespec start;
    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    long long prime_count = 0;
    for (long long value = 2; value <= n; value++) {
        prime_count += is_prime(value);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    printf("mode,sequential\n");
    printf("n,%lld\n", n);
    printf("processes,1\n");
    printf("prime_count,%lld\n", prime_count);
    printf("time_seconds,%.9f\n", elapsed_seconds(start, end));

    return EXIT_SUCCESS;
}
