# Thrax experiment

This is an experiment to use [thrax](https://www.openfst.org/twiki/bin/view/GRM/ThraxQuickTour) to implement some of the [transliteration rules here](https://docs.google.com/document/d/1ZmhFLZsgvNTGT1jIQZOFpXP-RnVXgjT9cAxj7j7hp3Q/edit?tab=t.0).

## Running the experiment

The FSTs are defined in a thrax grammar file at `my-thrax.grm`.  To run them:

1. `brew install thrax`
1. `thraxmakedep my-thrax.grm` (and ignore the syntax warning), only necessary
   when you first run the grammar and when you modify imports.
1. `make`
1. `cat simple-examples.txt | thraxrewrite-tester --noutput=25 --far=my-thrax.far --rules=TRANSLITERATOR`

