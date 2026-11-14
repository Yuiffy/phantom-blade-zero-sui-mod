"""Local data and tool locations. No personal installation paths are bundled."""
import os
from pathlib import Path
REPOSITORY = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get('PBZ_VOICE_WORKSPACE', str(REPOSITORY/'private/voice-workspace'))).resolve()
TOOLS = Path(os.environ.get('PBZ_VOICE_TOOLS', str(ROOT/'research/Bladesmith-tools/Bladesmith/tools'))).resolve()
def game_root():
    value = os.environ.get('PBZ_GAME_ROOT')
    if not value:
        raise ValueError('Set PBZ_GAME_ROOT to your local PBZ Steam installation')
    return Path(value).resolve()
def settings_path():
    if os.environ.get('PBZ_GAME_SETTINGS'):
        return Path(os.environ['PBZ_GAME_SETTINGS']).resolve()
    return Path(os.environ['LOCALAPPDATA'])/'ProjectPBZ/Saved/Config/Windows/GameUserSettings.ini'
