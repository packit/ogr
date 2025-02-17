For re-recording tests in this directory take and export the `FORGEJO_TOKEN` from Bitwarden item _Forgejo test server - for recording unit tests_ -> integration tests token.

Re-recording a test could fail if a repo (or any other resource) already exists and the test expects to create it. So be sure to met the test conditions before starting recording.

Also remember to remove any recorded artifact (looking at `test_data/name_of_the_test.yml`) before starting re-recording the test!
