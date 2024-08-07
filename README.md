# AI for Software Engineering

Generate source code mutants for python using a LLM.

## Installation

1. Clone the git repository:

	```sh
	git clone https://github.com/robert-oleynik/AI4SE-Mutation-Testing mutator
	```

2. Install this tool to your system:

	```sh
	pip install -e ./mutator
	```

	**Note:** You may want to run this and the following steps inside a `venv`.

3. Test the tool is installed successfully:

	```
	mutator --help
	mutator-runner --help
	```

	**Note:** The second command is required to execute the test and is installed as part of this project.

## Usage

This tool provides two main capabilities:

1. Generating and testing mutants for a software project.
2. Collect datasets from repositories and LoRa-finetuning on these datasets.

Both expect projects with following structure:

- `src/` contains all source files
- `tests/` contains all test files

### Generating and Testing Mutants

To generate mutants, this tool will follow the following steps:

1. Select all functions provided in the source files.
2. Remove all function not matching the filter expression. We will refer to these functions
   as source functions.
3. Generate mutants with all generator and generator config combinations.
4. Mark all duplicate mutants.
5. Run tests for all unique mutants.

#### Generators

Generators are functions, which transform source functions into mutants or mutated functions
with the usage of LLMs. The generators used in this project can be divided into two groups:

1. Generating mutants based on function signature and some extra information:

	- The first and most basic generator is the `docstring` generator. This generator
	  will prompt the LLM only with the signature and docstring.
	- The second generator `comment_rewrite` will additionally write the original
	  function commented out before the member function signature.
	- The `comment_rewrite_no_context` generator is a variation of the previous generator,
	  that does not provide context for the surrounding class.

2. Reusing parts of the existing implementation and prompting the LLM to rewrite parts of it:

	- The `prefix` generator will arbitrarily cut off the source function after a random token
	  and prompt the LLM with this result.
	- The `infilling` generator will work similarly using the same context. But instead of
	  cutting of tokens, it relies on TreeSitter to sample expressions or statements of the source
	  function and prompt the LLM to regenerate them.

#### Generator Configs

While using different prompts is one approach for receiving different mutants, we can also
modify the arguments passed to the LLMs generation method. We will refer to these arguments as
generator configs. In addition to the LLM arguments these configs also contains the number of
retries/repetitions a generator is supposed to do. Therefore, we provide following configs:

- `multi_sample` prompts the LLM to return multiple return sequences with sampling enabled.
- `beam_search` prompts the LLM to return multiple return sequences with beam search and
  sampling enabled.
- For each of the above, two additional configs with suffixes `_cold` and `_hold`, that set the
  temperature lower and higher, respectively.

Each config will produce the same number of mutants - 8 per source function.

#### Generating Mutants

To generate mutants, we will first need a project we want to test. For this, we will use the
Flask repository:

```sh
git clone https://github.com/pallets/flask
cd flask
```

Now we can use our tool on this repository to generate mutants.
We will start with the `infilling` generator with the `multi_sample`.
These can be set by the `-g/--generator` and `-c/--config` respectively.

```
mutator generate --generator infilling --config multi_sample --filter "flask.app:Flask.*"
```

> **Note:**
>
> - We use a simple globing syntax to filter with functions. This is necessary as the generation
>   testing may take some time.This globing reuses following syntax:
>
>   1. Each function is converted into construct following a syntax like
>      `<module path>:[<class name>.]<function_name>`
>   2. Each specified filter is converted into a RegEx by escaping `.` and replacing `*`
>      with `.*`. In addition, these filter allow a `!` in the beginning to mark negative filter.
>   3. We will match all functions against these filter and exclude all functions matching
>      negative filters.

Some other important flags for generating mutants:

- `-o/--out-dir` Change the directory to write the mutants to.
- `--clean` Removes all old mutants.
- `-m/--model` Change the LLM model to use. **Note:** this may cause compatibility issues.

#### Testing Mutants

To execute the test suite for each mutant we generate we can use the `mutator test` command.
It is important to note that each mutant has a timeout of `60s` this value can be changed by
using the `--timeout` flag.
Like `mutator generate` the `-o/--out-dir` can be used to change mutants work directory.

#### Inspect Results

The results of this test run can be viewed with `mutator inspect`.
This will open a TUI application showing the mutant as a diff and some additional
information including test output.
Use the list on the left to select a source function, the horizontal arrow keys to
select a mutant and ctrl + the horizontal arrow keys to cycle through the LLM's output stages.
Like `mutator generate` and `mutator test` the `-o/--out-dir` can be used to change
mutants work directory.

### Fine-Tuning

In some context, it is beneficial to use fine-tuning for improving LLM results.
To do so, this tool provides some utilities from collecting datasets to training the model.

#### Generating Datasets

As we already discussed we have multiple approaches for generating prompts.
Because of this, generating datasets need to account for the different input formats.

In the following we will generate a dataset from flask repository.
To do so, we will use a bare git repository of flask.

```sh
git clone --bare https://github.com/pallets/flask
```

To collect samples from this repository, we can use `mutator collect` as following:

```sh
mutator collect --bare ./flask.git --generator "infilling"
```

This will collect mutants from the source files and format these for the `infilling`
generator. While it is possible to specify multiple generators, it is not recommended.
In addition, it is also possible to specify multiple bare git repositories.
It is also possible to use normal git repositories using the `--repository` flag
instead.

These samples can be filtered by using following:

- `--max-dloc` Maximum change in lines of code (LOC) from source to mutant.
- `--max-loc-ratio` Maximum ratio between source and mutant LOC (`>1` means the
  mutant has more lines the source).
- `--min-prompt-loc` Minimum LOC for the generated prompt.
- `--max-prompt-loc` Maximum LOC for the generated prompt.

It is recommended to use these options in combination with `--update`.
This flag will load the dataset at `<out_dir>/data`, apply the limits and store
the result in `<out_dir>/data-updated`.
Using this command looks like:

```sh
mutator collect --update --max-dloc 10
```

#### Run Fine-Tuning

We can use the generated dataset with the following sub command:

```sh
mutator train --dataset "<collect_out_dir>/data-updated"
```

For more details on the available arguments see `mutator train --help`.
In addition, it is worthy to note, that the directory specified with
`--dataset` is the `data` or `data-updated` subdirectory of the output
directory specified with `collect`.

#### Evaluating Training

To evaluate the loss per training sample use the following command:

```sh
mutator train-result --dir out/model --dataset out/dataset/data-updated
```

## Development

> This section contains tools used and the recommended project setup for development.
> It is not mandatory for running the tool.

Required tools:

- [pyright](https://github.com/microsoft/pyright) for type checking
- [ruff](https://github.com/astral-sh/ruff) for linting

Install required dependencies:

```sh
# Create a venv
python3 -m venv venv
# Activate venv
source ./venv/bin/activate
# Install package dependencies
pip install -e .
```
