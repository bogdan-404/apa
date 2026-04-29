.PHONY: all clean benchmark

all:
	$(MAKE) -C sequential
	$(MAKE) -C parallel

clean:
	$(MAKE) -C sequential clean
	$(MAKE) -C parallel clean
	rm -f report/results.csv report/figures/*.svg

benchmark: all
	python3 report/scripts/run_benchmarks.py
