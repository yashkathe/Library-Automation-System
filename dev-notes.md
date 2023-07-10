
## Setting Virtual Environment


# Save packages to requirement.txt

```bash

pip3 freeze > requirements.txt
```

```bash

#activate venv

python3 -m venv directory-name

cd directory-name/

source bin/activate

pip install -r requirements.txt

#deactivate venv

deactivate

```
## Setting Environment Variables

_For Linux Environments_

```bash

# in virtual environemnts create . env file

touch .env

# Now save your secret

export KEY="mysecretkey_12345"

# Save this file in vevn

source .env

```


```python
import os

os.environ.get("KEY")
```
