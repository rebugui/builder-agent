"""
알림 모듈
새 게시글이 감지되면 팝업 및 소리로 알림을 제공합니다.
Windows, macOS, Linux 모두 지원합니다.
"""

import logging
import platform
import subprocess
from typing import Dict, List

logger = logging.getLogger(__name__)


class Notifier:
    """알림 제공 클래스 - OS 네이티브 알림"""

    def __init__(self, app_name: str = "ISMS-P 알림이"):
        self.app_name = app_name
        self.sound_enabled = True

    def notify_new_posts(self, new_posts: List[Dict[str, str]]) -> None:
        """새 게시글 알림 표시"""
        if not new_posts:
            return

        count = len(new_posts)
        if count == 1:
            post = new_posts[0]
            title = f"새 글: {post['title'][:30]}..."
            message = f"{post.get('category', '')} | {post.get('date', '')}\n{post['title']}"
        else:
            title = f"새 글 {count}개 도착!"
            message = "\n".join([f"• {p['title'][:40]}" for p in new_posts[:5]])
            if count > 5:
                message += f"\n...외 {count - 5}개"

        self.show_notification(title, message)

        if self.sound_enabled:
            self.play_sound()

    def show_notification(self, title: str, message: str, timeout: int = 10) -> None:
        """
        팝업 알림 표시 (OS 네이티브)

        Args:
            title: 알림 제목
            message: 알림 메시지
            timeout: 표시 시간 (초)
        """
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                self._notify_macos(title, message)
            elif system == "Linux":
                self._notify_linux(title, message)
            elif system == "Windows":
                self._notify_windows(title, message, timeout)
            else:
                logger.warning(f"지원하지 않는 OS: {system}")

        except Exception as e:
            logger.error(f"알림 표시 실패: {e}")
            # Fallback: 콘솔 출력
            print(f"\n[알림] {title}")
            print(f"{message}\n")

    def _notify_macos(self, title: str, message: str) -> None:
        """macOS 터미널 알림 (osascript)"""
        # osascript를 사용한 알림 창
        script = f'''
        tell application "System Events"
            activate
        end tell

        display dialog "{message}" ¬
            with title "{title}" ¬
            buttons {{"확인"}} ¬
            default button "확인" ¬
            with icon note
        '''
        subprocess.run(['osascript', '-e', script], check=False)

    def _notify_linux(self, title: str, message: str) -> None:
        """Linux notify-send"""
        subprocess.run([
            'notify-send',
            title,
            message
        ], check=False)

    def _notify_windows(self, title: str, message: str, timeout: int = 10) -> None:
        """Windows 알림"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title=title,
                msg=message,
                duration=timeout,
                threaded=True
            )
        except ImportError:
            # Fallback: PowerShell Balloon Tip
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text id="1">{title}</text>
                        <text id="2">{message}</text>
                    </binding>
                </visual>
            </toast>
            "@

            Add-Type -AssemblyName PresentationFramework
            $msg = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ISMS-P")
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            $msg.Show($toast)
            '''
            subprocess.run(['powershell', '-Command', ps_script], check=False)

    def play_sound(self) -> None:
        """알림 소리 재생"""
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"],
                    check=False,
                    capture_output=True
                )
            elif system == "Linux":
                subprocess.run(
                    ["aplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                    check=False,
                    capture_output=True
                )
            elif system == "Windows":
                try:
                    import winsound
                    winsound.Beep(880, 200)
                    winsound.Beep(1100, 200)
                except ImportError:
                    pass

        except Exception as e:
            logger.debug(f"소리 재생 실패: {e}")


# 테스트용 함수
def test_notification():
    """알림 테스트"""
    notifier = Notifier()
    notifier.show_notification(
        "ISMS-P 알림 테스트",
        "새 글이 등록되었습니다.\n\n(정보공유) 2025 SW 공급망 보안체계 진단 서비스 모집공고\n2025-06-02",
        timeout=5
    )


if __name__ == '__main__':
    test_notification()
