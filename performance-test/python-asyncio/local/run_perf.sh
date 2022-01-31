ulimit -Sn 10000
#Argtest

../../scripts/perf_test.py x x x x x --only-header
for m in 1 10
do
for n in 1 10
do
for o in 1 10
do
../../scripts/perf_test.py "ftl-events -i inventory${n}.yml rules${o}.yml -v events${m}.yml" ftl-events ${m} ${n} ${o} --no-header
done
done
done
