#!/usr/bin/env python3
"""为 ToonFlow Web 入口注入 crypto.randomUUID polyfill。

HTTP 公网地址不是安全上下文，Chromium 不提供 crypto.randomUUID，
ToonFlow 前端会在启动时报 `crypto.randomUUID is not a function`。
幂等：已存在 randomUUID 时直接退出。
"""
import sys

POLY = '''    <script>
      (function () {
        try {
          if (!window.crypto) window.crypto = {};
          if (typeof window.crypto.randomUUID !== "function") {
            window.crypto.randomUUID = function () {
              var b = new Uint8Array(16);
              if (window.crypto.getRandomValues) window.crypto.getRandomValues(b);
              else for (var i = 0; i < 16; i++) b[i] = Math.floor(Math.random() * 256);
              b[6] = (b[6] & 0x0f) | 0x40;
              b[8] = (b[8] & 0x3f) | 0x80;
              var h = Array.prototype.map.call(b, function (x) { return ("0" + x.toString(16)).slice(-2); }).join("");
              return h.slice(0, 8) + "-" + h.slice(8, 12) + "-" + h.slice(12, 16) + "-" + h.slice(16, 20) + "-" + h.slice(20);
            };
          }
        } catch (e) {}
      })();
    </script>
'''


def main(path: str) -> int:
    with open(path, encoding='utf-8') as f:
        s = f.read()
    if 'randomUUID' in s:
        return 0
    if '<head>' not in s:
        print('toonflow-randomuuid: <head> not found', file=sys.stderr)
        return 1
    s = s.replace('<head>', '<head>\n' + POLY, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(s)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1]))
