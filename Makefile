all: test

test:
	nosetests

dev:
	pip install -r requirements.txt
	python setup.py develop

install:
	python setup.py install

coverage:
	nosetests tests --with-coverage --cover-package=ginkgo

build_pages:
	export branch=$$(git status | grep 'On branch' | cut -f 4 -d ' '); \
	git checkout gh-pages; \
	git commit --allow-empty -m 'trigger pages rebuild'; \
	git push origin gh-pages; \
	git checkout $$branch
