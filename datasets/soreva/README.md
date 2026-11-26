---
language:
- af  
- bag  
- bas  
- bax  
- bbj  
- bdh  
- bfd  
- bkh  
- bkm  
- bqz  
- byv  
- dua  
- eto  
- etu  
- ewe  
- ewo  
- fmp  
- fub  
- fuc  
- gya  
- ha  
- ibo  
- isu  
- ker  
- kqs  
- ksf  
- lin  
- lns  
- lem  
- mcp  
- mg  
- mua  
- nda  
- nhh  
- nla  
- nso  
- pcm  
- swa  
- tvu  
- twi  
- vut  
- wol  
- xho  
- yat  
- yav  
- ybb  
- yor  
- zul  
license: cc-by-4.0
task_categories:
- text-to-speech
- automatic-speech-recognition

---

# SOREVA

## Dataset Description


- **Total amount of disk used:** ca. 403.3 MB


**SOREVA** (*Small Out-of-domain Resource for Various African languages*) is a multilingual speech dataset designed for the **evaluation** of text-to-speech (TTS) and speech representation models in **low-resource African languages**.
Comming from Goethe Institut intiative of collecting 150 samples(Audio and transcription) for about 49 africain languages and dialectes
This dataset specifically targets **out-of-domain generalization**, addressing the lack of evaluation sets for languages typically trained on narrow-domain corpora such as religious texts.


SOREVA includes languages from across Sub-Saharan Africa, including:

- **Standard languages**:  
  *`Afrikaans`, `Hausa`, `Yoruba`, `Igbo`, `Lingala`, `Kiswahili`, `isiXhosa`, `isiZulu`, `Wolof`*

- **Dialectal & minor languages**:  
  *`Bafia`, `Bafut`, `Baka`, `Bakoko`, `Bamun`, `Basaa`, `Duala`, `Ejagham`, `Eton`, `Ewondo`, `Fe`,  
  `Fulfulde`, `Gbaya`, `Ghamála`, `Isu`, `Kera`, `Kom`, `Kwasio`, `Lamso`, `Maka`, `Malagasy`, `Medumba`,  
  `Mka`, `Mundang`, `Nda`, `Ngiemboon`, `Ngombala`, `Nomaande`, `Nugunu`, `Pidgin`, `Pulaar`,  
  `Sepedi`, `Tuki`, `Tunen`, `Twi`, `Vute`, `Yambeta`, `Yangben`, `Yemba`, `Éwé`*



## How to use & Supported Tasks

### How to use

The `datasets` library allows you to load and pre-process your dataset in pure Python, at scale. The dataset can be downloaded and prepared in one call to your local drive by using the `load_dataset` function. 

For example, to download the Hausa Nigeria config, simply specify the corresponding language config name (i.e., "ha_ng" for Nigeria):
```python
from datasets import load_dataset
#Load a specific language (e.g., 'ha_ng' for Hausa Nigeria)
dataset = load_dataset("OlameMend/soreva", "ha_ng", split="test")
```

Load all languages together
```python
from datasets import load_dataset 
dataset = load_dataset("OlameMend/soreva", "all", split="test")

```
### 1. Out-of-domain TTS & ASR model Evaluation

Getting Audio and Transcription 

You can easily access and listen to audio samples along with their transcriptions:

```python
from datasets import load_dataset
from IPython.display import Audio

#Load the dataset for a specific language, e.g., "ha"
soreva = load_dataset("OlameMend/soreva", "ha_ng", split='test' , trust_remote_code=True)

#Access the first example's audio array and sampling rate
audio_array = soreva[0]['audio']['array']        # audio data as numpy array
sr = soreva[0]['audio']['sampling_rate']         # sampling rate

#Print the corresponding transcription or use it for TTS inference for evaluation
print(soreva[0]['transcription'])

#Play the audio in a Jupyter notebook
Audio(audio_array, rate=sr)
```

## Dataset Structure

We show detailed information the example configurations `ewo_cm` of the dataset.
All other configurations have the same structure.

### Data Instances

**ewo_cm**
- Size of downloaded dataset files: 14 MB


An example of a data instance of the config `ewo_cm` looks as follows:

```
{'path': '/home/mendo/.cache/huggingface/datasets/downloads/extracted/3f773a931d09d3c4f9e9a8643e93d191a30d36df95ae32eedbafb6a634135f98/cm_ewo_001.wav',
 'audio': {'path': 'cm_ewo/cm_ewo_001.wav',
  'array': array([-0.00518799, -0.00698853, -0.00814819, ..., -0.02404785,
         -0.02084351, -0.02062988]),
  'sampling_rate': 16000},
 'transcription': 'mbembe kidi',
 'raw_transcription': 'mbəmbə kídí',
 'gender': 0,
 'lang_id': 15,
 'language': 'Ewondo'}
```

### Data Fields

The data fields are the same among all splits.
- **path** (`str`):  Path to the audio file.
- **audio** (`dict`):  Audio object including:
  - **array** (`np.array`):  Loaded audio waveform as float values.
  - **sampling_rate** (`int`):  Sampling rate of the audio.
  - **path** (`str`):  Relative path inside the archive or dataset.
- **transcription** (`str`):  Normalized transcription of the audio file.
- **raw_transcription** (`str`):  Original non-normalized transcription of the audio file.
- **gender** (`int`):    Class ID of gender (0 = MALE, 1 = FEMALE, 2 = OTHER).
- **lang_id** (`int`):   Class ID of the language.
- **language** (`str`):  Full language name corresponding to the lang_id.


### Data Splits

Currently, as this is the first initiative, we only provide a **test** split containing approximately **150** audio samples.

Other splits such as **train** and **validation** are not included at this stage but are expected to be added through community contributions and continuous dataset development.

This initial test split allows evaluation and benchmarking, while the dataset will evolve to include more comprehensive splits in the future.
## Dataset Creation

The data were collected by the Goethe-Institut and consist of 150 audio samples with corresponding transcriptions across 48 African languages and dialects.

## Considerations for Using the Data

### Social Impact of Dataset

This dataset is meant to encourage the development of speech technology in a lot more languages of the world. One of the goal is to give equal access to technologies like speech recognition or speech translation to everyone, meaning better dubbing or better access to content from the internet (like podcasts, streaming or videos).

### Discussion of Biases
For all languages, only male voice is represented


### Other Known Limitations
Certains transcript only contain single word instead of complete sentence; others line of transcription has deux sentences(variance) for the same audio


## Additional Information

All datasets are licensed under the [Creative Commons license (CC-BY)](https://creativecommons.org/licenses/).

### Citation Information

@misc{
      title={Soreva: Small Out-of-domain resource for various africain languages}, 
      author={Leo Mendo Olame},
      year={2025},
}




### Contact

For all questions contact [@LeoMendo](leomendoolame@gmail.com) .
