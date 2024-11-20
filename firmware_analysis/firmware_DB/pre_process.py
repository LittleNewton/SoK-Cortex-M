from pathlib import Path
import shutil
import re
from loguru import logger

# 配置 loguru
logger.add("firmware_organizer.log", rotation="10 MB")


class FirmwareOrganizer:
    def __init__(
        self,
        firmware_root: Path,
        disassembly_root: Path,
        output_root: Path
    ):
        self.firmware_root = Path(firmware_root)
        self.disassembly_root = Path(disassembly_root)
        self.output_root = Path(output_root)

        # 验证输入路径
        if not self.firmware_root.exists():
            logger.error(f"固件路径不存在: {self.firmware_root}")
            raise FileNotFoundError(f"固件路径不存在: {self.firmware_root}")
        if not self.disassembly_root.exists():
            logger.error(f"反汇编路径不存在: {self.disassembly_root}")
            raise FileNotFoundError(f"反汇编路径不存在: {self.disassembly_root}")

    def parse_firmware_name(
        self,
        filename: str
    ) -> tuple:
        """Parse firmware filename to get id and md5."""
        parts = filename.split('@')
        if len(parts) >= 2:
            if len(parts) > 2:
                logger.warning(f"文件名包含多个MD5值: {filename}, 将只使用第一个MD5")
            return parts[0], parts[1]
        logger.warning(f"无法解析的文件名格式: {filename}")
        return None, None

    def collect_firmware_files(
        self
    ) -> dict:
        """收集固件文件信息，返回 {vendor: [(id, md5, path), ...]} 的字典"""
        firmware_files = {}

        logger.info(f"开始扫描固件目录: {self.firmware_root}")
        for vendor_dir in self.firmware_root.iterdir():
            if vendor_dir.is_dir():
                vendor_name = vendor_dir.name
                firmware_files[vendor_name] = []
                logger.info(f"处理厂商目录: {vendor_name}")

                for fw_file in vendor_dir.glob('*'):
                    if fw_file.is_file():
                        fw_id, fw_md5 = self.parse_firmware_name(fw_file.name)
                        if fw_id and fw_md5:
                            firmware_files[vendor_name].append(
                                (fw_id, fw_md5, fw_file))
                            logger.debug(f"找到固件: {fw_id}@{fw_md5}")
                        else:
                            logger.warning(f"跳过无效的固件文件: {fw_file}")

                if not firmware_files[vendor_name]:
                    logger.warning(f"厂商 {vendor_name} 目录下没有找到有效的固件文件")

        return firmware_files

    def find_disassembly_file(
        self, fw_id: str,
        fw_md5: str
    ) -> Path:
        """在反汇编目录中查找对应的反汇编文件"""
        pattern = f"{fw_id}@{fw_md5}"
        matching_files = list(self.disassembly_root.glob(f"{pattern}*"))

        if not matching_files:
            logger.error(f"未找到固件 {fw_id} (MD5: {fw_md5}) 的反汇编文件")
            # return None

        if len(matching_files) > 1:
            logger.error(f"固件 {fw_id} (MD5: {fw_md5}) 找到多个匹配的反汇编文件，使用第一个: {
                         matching_files} stop.")

        return matching_files[0]

    def organize_files(self):
        """组织文件到新的结构"""
        logger.info("开始组织文件...")

        # 确保输出目录存在
        self.output_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建输出目录: {self.output_root}")

        # 收集固件信息
        firmware_files = self.collect_firmware_files()

        # 跟踪重复的ID
        seen_ids = {}

        # 按照新的结构组织文件
        for vendor, files in firmware_files.items():
            vendor_dir = self.output_root / vendor
            vendor_dir.mkdir(exist_ok=True)
            logger.info(f"处理厂商 {vendor} 的文件，共 {len(files)} 个")

            for fw_id, fw_md5, fw_path in files:
                # 检查ID重复
                if fw_id in seen_ids:
                    logger.warning(f"发现重复的固件ID: {fw_id}")
                    logger.warning(f"  之前的MD5: {seen_ids[fw_id]}")
                    logger.warning(f"  当前的MD5: {fw_md5}")
                seen_ids[fw_id] = fw_md5

                # 为每个固件创建目录
                fw_dir = vendor_dir / fw_id
                fw_dir.mkdir(exist_ok=True)
                logger.info(f"处理固件: {fw_id}")

                try:
                    # 复制固件文件
                    shutil.copy2(fw_path, fw_dir / fw_id)
                    logger.debug(f"复制固件文件: {fw_path} -> {fw_dir / fw_id}")

                    # 创建 hash 文件
                    with open(fw_dir / fw_md5, "w") as f:
                        f.write(fw_md5)
                    logger.debug(f"创建MD5文件: {fw_dir / 'md5'}")

                    # 查找并复制反汇编文件
                    asm_file = self.find_disassembly_file(fw_id, fw_md5)
                    if asm_file:
                        shutil.copy2(asm_file, fw_dir / f"{fw_id}.asm")
                        logger.debug(
                            f"复制反汇编文件: {asm_file} -> {fw_dir / f'{fw_id}.asm'}")

                except Exception as e:
                    logger.error(f"处理固件 {fw_id} 时发生错误: {str(e)}")

        logger.info("文件组织完成！")


def main():
    try:
        # 设置路径
        firmware_root = Path("firmware")
        disassembly_root = Path("firmware-disassembly")
        output_root = Path("organized_firmware")

        logger.info("开始固件归档任务")
        logger.info(f"固件目录: {firmware_root}")
        logger.info(f"反汇编目录: {disassembly_root}")
        logger.info(f"输出目录: {output_root}")

        # 创建组织器实例并运行
        organizer = FirmwareOrganizer(
            firmware_root, disassembly_root, output_root)
        organizer.organize_files()

        logger.info("任务完成！")

    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    main()
