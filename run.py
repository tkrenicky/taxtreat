from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from taxtreat_cz.crawler import Crawler
from taxtreat_cz.build_db import build
if __name__=='__main__':
    Crawler(ROOT).run()
    build(ROOT)
