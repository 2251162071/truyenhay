import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def get_vpn_status(vpn_name):
    """
    Kiểm tra trạng thái của VPN.
    Args:
        vpn_name (str): Tên của VPN cần kiểm tra.

    Returns:
        bool: True nếu VPN đang được bật, False nếu VPN đang tắt.
    """
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE,STATE", "connection", "show", "--active"],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        # Kiểm tra nếu VPN đang hoạt động
        active_connections = result.stdout.strip().split('\n')
        for connection in active_connections:
            name, conn_type, state = connection.split(':')
            if name == vpn_name and conn_type == "vpn" and state == "activated":
                logger.info(f"VPN {vpn_name} đang được bật.")
                return True
        logger.info(f"VPN {vpn_name} đang tắt.")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi kiểm tra trạng thái VPN: {e}")
        raise

def toggle_vpn(vpn_enabled, vpn_name=None):
    """
    Bật hoặc tắt VPN.
    Args:
        vpn_enabled (bool): Trạng thái hiện tại của VPN.
        vpn_name (str, optional): Tên VPN. Mặc định lấy từ biến môi trường VPN_NAME.

    Returns:
        bool: Trạng thái VPN sau khi thay đổi.
    """
    vpn_name = vpn_name or os.getenv('VPN_NAME')
    if not vpn_name:
        raise ValueError("VPN_NAME environment variable is not set.")

    try:
        # current_status = get_vpn_status(vpn_name)
        # if vpn_enabled == current_status:
        #     logger.info(f"VPN {vpn_name} đã ở trạng thái mong muốn ({'Enabled' if vpn_enabled else 'Disabled'}).")
        #     return vpn_enabled

        if not vpn_enabled:
            logger.info("Enabling VPN...")
            subprocess.run(["nmcli", "connection", "up", vpn_name], check=True)
            logger.info(f"VPN {vpn_name} đã được bật.")
        else:
            logger.info("Disabling VPN...")
            subprocess.run(["nmcli", "connection", "down", vpn_name], check=True)
            logger.info(f"VPN {vpn_name} đã được tắt.")
        return not vpn_enabled
    except subprocess.CalledProcessError as e:
        logger.error(f"Lỗi khi bật/tắt VPN: {e}")
        raise
