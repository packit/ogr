# Running tests via `tmt`

## Running tests locally

> [!NOTE]
>
> This is not the recommended way to run the tests as it pollutes the local
> environment.

Run:

    $ tmt -v run -a provision -h local

> [!WARNING]
>
> `prepare` step of the `tmt` can ask for privilege escalation to install the
> required dependencies

## Running tests locally in a container

It may be needed to install the `container` provisioning plugin:

    $ sudo dnf install tmt-provision-container

Afterwards you can run the tests via:

    $ tmt -v run -a provision -h container

Additionally you can also limit what tests are being run by setting the
`TEST_TARGET` environment variable:

    # For example this limits to only Forgejo tests
    $ tmt -v run -e TEST_TARGET=integration/forgejo/ -a provision -h container

## Regenerating requre responses via `tmt`

It is also possible to regenerate requre responses, but there are some
adjustments needed and they also introduce some consequences.

`tmt` by default _prunes_ the tree after finishing the test execution, since it
copies the whole test repo for execution of the tests, i.e., to save resources.

Therefore even when passing the tokens to the `tmt` test execution, the requre
responses are generated, but at the same time they are deleted during the `tmt`
clean up.

This can be avoided by instructing tmt to keep the work directory after the test
execution is finished:

    # For example to generate Forgejo responses
    $ tmt -vv \
        run -a -k \
        -e FORGEJO_TOKEN=$FORGEJO_TOKEN -e TEST_TARGET=integration/forgejo/ \
          provision -h container \
          plan -n full \
          report -h display

Explanation of the `tmt` command:

- Execute `tmt` with increased verbosity (`-vv`)
- _Run_ _all_ the test steps while _keeping_ the files after the tests finish
  (skips pruning), passing Forgejo token, and limiting only to Forgejo tests
- _Provision_ a container for running the tests
- Limit the test execution only to the `full` tmt plan (skip rev-dep tests)

> [!TIP]
>
> It might be more user-friendly for you to pass the tokens via a dotenv file
> with environment variables.
>
> 1. Create a file with environment variables:
>
>    ```
>    cp .env.template .env
>    ```
>
> 2. Populate `.env` with tokens
> 3. Adjust the tmt command:
>
>    ```
>    tmt -vv \
>      run -a -k -e @.env \
>        provision -h container \
>        plan -n full \
>        report -h display
>    ```
>
> You can still override variables, if needed, after specifying the environment
> file.

Afterwards the generated responses can be found in the test directory
(`<ID>` varies):

    /var/tmp/tmt/<ID>/plans/full/discover/default-0/tests/

> [!WARNING]
>
> Don't forget to clean the directories afterwards. This can be done by running
> the `tmt clean` command. You can either:
>
> - clean the last run with `tmt clean -l`, or
> - specify a concrete ID of the run with `tmt clean --id <ID>`.

## Additional resources

For more info see:

- https://packit.dev/docs/testing-farm/
- [tmt @ DevConf 2021 slides](https://static.sched.com/hosted_files/devconfcz2021/37/tmt-slides.pdf)
- [fmf docs](https://fmf.readthedocs.io)
- [tmt docs](https://tmt.readthedocs.io)
