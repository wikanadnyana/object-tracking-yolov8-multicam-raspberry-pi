## Acrobat :

1. inference packages from main system into venv, got an answer use this command :

```shell
python -m venv --system-site-packages env
```

2. <code>PyQt5</code> installation, first problem solve by install the package in main system using _apt_ :

```
sudo apt install python3-pyqt5
```

3. the inference version venv for pyqt package throw an error, solution setup for the path in os.environ QT_QPA_PLATFORM_PLUGIN_PATH into :

```
'/usr/local/lib/python3.11/dist-packages/cv2/qt/plugins/platforms'
```

4. when install packages sometimes show the problem about <code>externally-managed-environment</code> :

```
sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED
sudo pip3 install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
```
