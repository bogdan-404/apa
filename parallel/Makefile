MPICC = mpicc
CFLAGS = -O2 -Wall -Wextra -std=c11
TARGET = prime_parallel

.PHONY: all clean run

all: $(TARGET)

$(TARGET): prime_parallel.c
	$(MPICC) $(CFLAGS) -o $(TARGET) prime_parallel.c

run: $(TARGET)
	mpirun -np 4 ./$(TARGET) 100000

clean:
	rm -f $(TARGET)
