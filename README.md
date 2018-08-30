# Jekyll Post Tool

This python3 script takes csv input files and outputs Jekyll markdown posts. Used for the Linaro Connect event website. Sessions and users are exported from a third party service and used to generate resource/talk posts.

## Prerequisites

- Jekyll static website
- CSV data to create Jekyll posts from
- Python3

This script was built for the Linaro Connect static website but could be adapted to take other formats of data as input - csv, json - and create Jekyll posts from them.

## Getting Started

### 1. Install Requirements

Install requirements from the requirements.txt file using:

```bash
$ pip3 install -r requirements.txt
```

This will install all the packages you need in order to run this script.

### 2. Modify script to use your export data

This script has been written to combine the data from a `sessions.csv` and `users.csv` file. You will need to change a few functions of the script to collect the data you need.


Look at this function and modify to grab the data from your export file.

```python
...
def grab_user_data_from_csv(self):
...
```

Modify to accordingly to fetch the data using the modified method below.


```python
...
def main(self):
...
```

Modify to pull the data from your data array.

```python
...
def create_jekyll_event_posts(self, sessions, users):
...
```
