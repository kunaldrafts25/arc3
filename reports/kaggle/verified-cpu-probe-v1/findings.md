# First CPU integration gate failed before extension execution

The direct-write probe omitted the final newline that IPython `%%writefile`
adds to the original notebook's harness patch. Git rejected the patch as corrupt
at line 10086. No model, GPU or competition gameplay was involved.

The probe builder now preserves that newline. A local regression test runs Git's
patch parser on the generated patch. CPU version 2 subsequently passed all seven
mechanical cases; final version 3 also checks the rendered prompt contract.
