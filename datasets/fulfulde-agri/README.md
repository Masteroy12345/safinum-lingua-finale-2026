---
dataset_info:
  features:
  - name: path
    dtype: audio
  - name: text
    dtype: string
  - name: gender
    dtype: string
  splits:
  - name: train
    num_bytes: 173915781.44
    num_examples: 1108
  - name: test
    num_bytes: 43428021.0
    num_examples: 278
  download_size: 180030427
  dataset_size: 217343802.44
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
---
