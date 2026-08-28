my-thrax.far: my-thrax.grm byte.far
	thraxcompiler --input_grammar=$< --output_far=$@ --save_symbols=true

byte.far: byte.grm 
	thraxcompiler --input_grammar=$< --output_far=$@ --save_symbols=true

clean:
	rm -f byte.far
