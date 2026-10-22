# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      ?= ../build/docs

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help api html Makefile

api:
	@sphinx-apidoc --force --maxdepth 1 --separate --implicit-namespaces --output-dir api/ ../src/amal/ ../src/amal/eda/ipxact_de/gui ../src/amal/eda/ipxact_de/web
	@sphinx-apidoc --force --maxdepth 1 --separate --implicit-namespaces --output-dir api/ ../src/org/

# HTML has a stable path for local use and CI artifacts.
html:
	@$(SPHINXBUILD) -b html -d "$(BUILDDIR)/doctrees" "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
