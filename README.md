# Any-Task BrainCo Data Collection — хост

Эта папка — отдельная минимальная копия **хостовой** части из `Teleop-Data-Collection`. Она записывает состояние G1, BrainCo рук и RGB камеры `ego_view`. Head/external camera, depth и телеметрия верхней части G1 в этом сценарии не записываются. Exporter спрашивает `Task to record:` и сохраняет набор данных в `outputs/<task>-<timestamp>/` относительно этой папки.

## Что находится в папке

- `launch_brainco_any_task_host_tmux.sh` — запускает на хосте exporter и окно просмотра камеры в tmux.
- `gear_sonic/scripts/brainco_data_exporter_any_task/` — сбор данных, DDS BrainCo и схема набора данных.
- `gear_sonic/scripts/run_data_exporter.py`, `gear_sonic/data/`, `gear_sonic/utils/data_collection/` — необходимые общие компоненты exporter.
- `gear_sonic/scripts/run_camera_viewer.py`, `gear_sonic/camera/` — просмотр `ego_view` и клиент камеры ZMQ.
- `gear_sonic/data/robot_model/model_data/g1/g1_29dof_with_hand.urdf` — модель для FK; секции визуальной геометрии удалены, поэтому меши не нужны.

На роботе остаётся исходный проект `/home/unitree/teleop-ws/Teleop-Data-Collection`; команды для него приведены ниже. Копировать хостовую папку на робота не требуется.

## Подготовка хоста

Нужны `uv`, `tmux`, доступ к роботу по сети и локальный `unitree_sdk2_python` (в исходной установке он расположен по соседству: `/home/nikita/Skoltech/MWS/unitree_sdk2_python`). Один раз создайте виртуальное окружение проекта с Python 3.10, активируйте его и установите зависимости:

```bash
cd /home/nikita/Skoltech/MWS/dataset_exporter_unitree
uv python install 3.10
uv venv .venv_data_collection --python 3.10
source .venv_data_collection/bin/activate
GIT_LFS_SKIP_SMUDGE=1 uv pip install -r requirements.txt
uv pip install -e ../unitree_sdk2_python
uv pip install --reinstall --no-deps opencv-python==4.11.0.86
```

Последняя команда обязательна: LeRobot устанавливает также `opencv-python-headless`, и после общей установки Python может загрузить сборку OpenCV без поддержки окон. Повторная установка `opencv-python` возвращает поддержку GUI для viewer. Проверка:

```bash
python -c "import cv2; print([line for line in cv2.getBuildInformation().splitlines() if 'GUI:' in line][0])"
```

В выводе должно быть `GUI: QT5`, а не `GUI: NONE`. Если после установки других пакетов снова появляется `GUI: NONE`, повторите команду `uv pip install --reinstall --no-deps opencv-python==4.11.0.86` в активированном окружении.

Окружение хранится в `.venv_data_collection/`. При каждом новом открытии терминала активируйте уже созданное окружение так:

```bash
cd /home/nikita/Skoltech/MWS/dataset_exporter_unitree
source .venv_data_collection/bin/activate
python --version
```

Команда `python --version` должна показать Python 3.10. Для выхода из окружения выполните `deactivate`. Скрипт `launch_brainco_any_task_host_tmux.sh` сам активирует это окружение в окнах tmux, поэтому перед запуском через tmux вручную выполнять `source` не обязательно.

Для голосовых подсказок нужен системный `espeak` (`sudo apt install espeak`). Без него сбор данных запускается, но голосовые подсказки могут не работать. Если готовое окружение из исходного проекта уже есть, можно передать его launcher через `DATA_COLLECTION_VENV=/home/nikita/Skoltech/MWS/Teleop-Data-Collection/.venv_data_collection`.

Интерфейс `wlp128s20f3` в примерах — сетевой интерфейс **хоста** для DDS BrainCo. При другом имени замените `PICO_INTERFACE`/`--brainco-network-interface` на своё. Адрес `192.168.50.132` — адрес робота, от которого приходят ZMQ потоки.

## Запуск через tmux

Сначала запустите процессы на роботе (см. ниже). Затем на хосте:

```bash
cd /home/nikita/Skoltech/MWS/dataset_exporter_unitree
ROBOT_HOST=192.168.50.132 \
PICO_INTERFACE=wlp128s20f3 \
bash launch_brainco_any_task_host_tmux.sh
tmux attach -t brainco_any_task_host
```

В окне `exporter` введите имя задачи. Окно `viewer` показывает `ego_view`. Переключение окон tmux: `Ctrl-b`, затем `n`/`p`; отсоединение: `Ctrl-b`, затем `d`.

Повторный запуск существующей сессии:

```bash
ROBOT_HOST=192.168.50.132 bash launch_brainco_any_task_host_tmux.sh --replace
```

Для запуска без окна просмотра: `ENABLE_CAMERA_VIEWER=0 ROBOT_HOST=192.168.50.132 bash launch_brainco_any_task_host_tmux.sh`. Адреса и порты можно переопределить переменными `CAMERA_HOST`, `SONIC_HOST`, `STATE_HOST`, `CAMERA_PORT`, `SONIC_PORT`, `STATE_PORT`; дополнительные параметры exporter — `EXPORTER_EXTRA_ARGS`. Окно просмотра требует графическую сессию на хосте.

## Хост: запуск по отдельности

Откройте два терминала после запуска процессов на роботе.

### Терминал 1 — data exporter

```bash
cd /home/nikita/Skoltech/MWS/dataset_exporter_unitree
source .venv_data_collection/bin/activate

python -m gear_sonic.scripts.brainco_data_exporter_any_task \
  --camera-host 192.168.50.132 \
  --camera-port 5555 \
  --sonic-zmq-host 192.168.50.132 \
  --sonic-zmq-port 5556 \
  --state-zmq-host 192.168.50.132 \
  --state-zmq-port 5557 \
  --brainco-network-interface wlp128s20f3 \
  --depth-camera-width 1280 \
  --depth-camera-height 720
```

Введите имя задачи в ответ на `Task to record:`. Данные появятся в `outputs/<task>-<timestamp>/`.

### Терминал 2 — просмотр ego-view

```bash
cd /home/nikita/Skoltech/MWS/dataset_exporter_unitree
source .venv_data_collection/bin/activate

python -m gear_sonic.scripts.run_camera_viewer \
  --camera-host 192.168.50.132 \
  --camera-port 5555 \
  --camera-streams ego_view \
  --no-depth \
  --grid-columns 1 \
  --no-motor-states
```

## Робот: запуск через tmux

На роботе используется **исходный** проект и его исходный launcher:

```bash
cd /home/unitree/teleop-ws/Teleop-Data-Collection
bash gear_sonic/scripts/launch_brainco_any_task_robot_tmux.sh
tmux attach -t brainco_any_task_robot
```

Для перезапуска существующей сессии:

```bash
bash gear_sonic/scripts/launch_brainco_any_task_robot_tmux.sh --replace
```

Как в исходной инструкции: если при запуске робот начинает странно двигаться с высокой частотой, остановите deploy и контейнер с daemon:

```bash
sudo docker stop 15f8798287b672dac5192885794060781cde1df1a969f78ff4ec77cb6e94f56c
```

## Робот: запуск по отдельности

Каждый блок запускается в отдельном терминале на роботе, в приведённом порядке.

### Терминал 1 — BrainCo service

```bash
cd /home/unitree/teleop-ws/Teleop-Data-Collection
bash gear_sonic/scripts/start_brainco_and_check.sh \
  --container g1-brainco-hand-server \
  --attempts 10 \
  --interface wlxfc23cd997021
```

### Терминал 2 — ego-view camera

```bash
source /home/unitree/GR00T-WholeBodyControl/.venv_camera/bin/activate
cd /home/unitree/teleop-ws/Teleop-Data-Collection

python -m gear_sonic.camera.composed_camera \
  --ego-view-camera realsense \
  --ego-view-device-id 243422071979 \
  --realsense-width 1280 \
  --realsense-height 720 \
  --no-realsense-depth \
  --fps 15 \
  --port 5555
```

### Терминал 3 — Pico manager

```bash
source /home/unitree/GR00T-WholeBodyControl/.venv_teleop/bin/activate
cd /home/unitree/teleop-ws/Teleop-Data-Collection

python -m gear_sonic.scripts.pico_manager_brainco_dexterous \
  --manager \
  --port 5556 \
  --target_fps 50 \
  --brainco_network_interface wlxfc23cd997021
```

### Терминал 4 — Gear Sonic deploy

```bash
export TensorRT_ROOT="$HOME/TensorRT"
cd /home/unitree/GR00T-WholeBodyControl/gear_sonic_deploy
source scripts/setup_env.sh
./deploy.sh --input-type zmq_manager real
```

## Управление эпизодами

- Левый grip + `A`: начать или закончить эпизод.
- Левый grip + `B`: сохранить текущий эпизод как discarded.
- Правый grip: поставить временную метку.
