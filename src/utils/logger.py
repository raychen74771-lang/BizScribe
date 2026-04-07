import logging
import os
from rich.logging import RichHandler
from rich.console import Console

console = Console()

def setup_logger(level="INFO"):
    # 确保 workspace 目录存在，用于存放审计日志
    workspace_dir = os.path.join(os.getcwd(), "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    
    log_file_path = os.path.join(workspace_dir, "bizscribe_audit.log")
    
    # 💎 FileHandler: 永久记录到本地文件 (黑匣子)
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    # 详细的文件日志格式，带上精确到毫秒的时间戳
    file_formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # 💎 RichHandler: 控制台的彩色输出 (保持原有美观)
    rich_handler = RichHandler(console=console, show_path=False)
    
    # 配置根 Logger
    logging.basicConfig(
        level=level, 
        format="%(message)s", 
        datefmt="[%X]", 
        handlers=[rich_handler, file_handler]
    )
    
    # 获取专属 logger
    logger = logging.getLogger("bizscribe")
    
    # 每次启动时在日志文件里打个标记，方便你查阅
    logger.info("="*40)
    logger.info("🚀 BizScribe 审计日志系统已启动")
    logger.info("="*40)
    
    return logger

logger = setup_logger()