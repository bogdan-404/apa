#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

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

static void compute_interval(long long n, int worker_index, int workers,
                             long long *start, long long *end)
{
    const long long first_value = 2;
    const long long total_values = n - first_value + 1;
    const long long base_size = total_values / workers;
    const long long remainder = total_values % workers;

    const long long local_size = base_size + (worker_index < remainder ? 1 : 0);
    const long long offset = worker_index * base_size +
                             (worker_index < remainder ? worker_index : remainder);

    *start = first_value + offset;
    *end = *start + local_size - 1;
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank = 0;
    int processes = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processes);

    if (processes < 2) {
        if (rank == 0) {
            fprintf(stderr, "Eroare: folositi cel putin 2 procese MPI (1 manager + workeri).\n");
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    if (argc != 2) {
        if (rank == 0) {
            fprintf(stderr, "Utilizare: mpirun -np <procese> %s <n>\n", argv[0]);
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    char *endptr = NULL;
    long long n = strtoll(argv[1], &endptr, 10);
    if (*endptr != '\0' || n < 2) {
        if (rank == 0) {
            fprintf(stderr, "Eroare: n trebuie sa fie un numar intreg >= 2.\n");
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    long long local_start = 0;
    long long local_end = 0;
    if (rank != 0) {
        compute_interval(n, rank - 1, processes - 1, &local_start, &local_end);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();

    long long local_count = 0;
    if (rank != 0) {
        for (long long value = local_start; value <= local_end; value++) {
            local_count += is_prime(value);
        }
    }

    long long total_count = 0;
    MPI_Reduce(&local_count, &total_count, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    double elapsed = MPI_Wtime() - start_time;
    double max_elapsed = 0.0;
    MPI_Reduce(&elapsed, &max_elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        printf("mode,parallel\n");
        printf("n,%lld\n", n);
        printf("processes,%d\n", processes);
        printf("prime_count,%lld\n", total_count);
        printf("time_seconds,%.9f\n", max_elapsed);
    }

    MPI_Finalize();
    return EXIT_SUCCESS;
}
