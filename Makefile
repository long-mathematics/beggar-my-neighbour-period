.PHONY: paper verify-native verify-all clean
paper:
	latexmk -pdf -interaction=nonstopmode -halt-on-error minimum_period.tex
verify-native:
	python3 native_z3_check.py --json verification/native_z3_fresh.json
	python3 backward_component.py --json verification/backward_fresh.json
	python3 check_rigidity.py --json verification/rigidity_fresh.json
verify-all:
	python3 prove_minimum.py --structural --json verification/minimum_fresh.json
	$(MAKE) verify-native
clean:
	latexmk -c
