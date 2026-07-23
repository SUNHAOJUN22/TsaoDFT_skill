# Batch DAG

Tasks declare dependencies, owner directory, expected artifacts, retry limit and acceptance gate. Independent jobs may run concurrently; dependent tasks cannot infer completion from file timestamps alone.
