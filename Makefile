.PHONY: paper verify-native verify-all classify-six crosscheck-six clean
paper:
	latexmk -pdf -interaction=nonstopmode -halt-on-error minimum_period.tex
verify-native:
	python3 native_z3_check.py --json verification/native_z3_fresh.json
	python3 backward_component.py --json verification/backward_fresh.json
	python3 verify_orbit_symmetry.py --json verification/orbit_symmetry_verification.json
	python3 check_rigidity.py --json verification/rigidity_fresh.json
classify-six:
	c++ -O3 -std=c++20 skeleton6.cpp -o skeleton6
	./skeleton6 skeleton6.tsv
	python3 classify_six.py --json verification/six_classification_full.json
	python3 enumerate_models.py --json verification/six_classification_models.json
	python3 backward_component.py --json verification/six_backward_component.json
	python3 verify_classification_reports.py
crosscheck-six:
	@for w in 111110 111100 111010 111000 110110 110100 101010; do \
		python3 crosscheck_skeletons.py --winner $$w --json verification/crosscheck_$$w.json || exit 1; \
	done
verify-all:
	python3 prove_minimum.py --structural --json verification/minimum_fresh.json
	$(MAKE) verify-native
	$(MAKE) classify-six
	$(MAKE) crosscheck-six
clean:
	latexmk -c
	rm -f skeleton6
