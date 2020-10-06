all: docs

docs: FORCE
	MSG="$(shell git log -1 --pretty=%B | tr -d '\n')"
	@echo $(MSG)
	pandoc README.md -o docs/README.rst; \
	cd docs/; \
	sphinx-apidoc -e -f -M -o ./ ../; \
	cd ~/code/pyb/docs/; \
	make html


publish: FORCE
	cd ~/pages/pyb/; \
	git rm -r *; \
	cp -r _build/html/* ~/pages/pyb/; \
	cd ~/pages/pyb; \
	touch .nojekyll; \
	git add *; \
	git add .nojekyll; \
	git commit -am "$(shell git log -1 --pretty=%B | tr -d '\n')"; \
	git push origin gh-pages; \
	cd ~/code/pyb

FORCE:
