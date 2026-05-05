"""
cache_manager.py — ระบบ Cache แบบ Thread-Safe

ไฟล์นี้จัดการ cache สำหรับผลลัพธ์การตรวจคำ/สะกดคำ
ใช้ threading.Lock ป้องกัน race condition (เมื่อหลาย request เข้ามาพร้อมกัน)

เหตุผลที่ต้องมี cache:
  - LanguageTool ตรวจคำช้า (~50-200ms ต่อคำ)
  - ผู้ใช้พิมพ์คำเดิมซ้ำบ่อย
  - Cache ช่วยลดเวลาตอบกลับเหลือ <1ms สำหรับคำที่เคยตรวจแล้ว

โครงสร้าง:
  - CacheManager: class สำหรับ cache 1 ประเภท (มี Lock + ขนาดจำกัด)
  - start_periodic_cleanup(): เริ่ม daemon thread ที่ล้าง cache ทุก 3 นาที
"""

import threading
import time
from typing import Any, Optional


class CacheManager:
    """
    Cache แบบ Thread-Safe ที่มีขนาดจำกัด (LRU-style eviction)
    
    การทำงาน:
      1. เก็บ key-value ใน dict ธรรมดา
      2. ใช้ Lock ป้องกันการอ่าน/เขียนพร้อมกันจากหลาย thread
      3. เมื่อ cache เต็ม (เกิน max_size) → ลบครึ่งเก่าออก
    
    ตัวอย่าง:
      cache = CacheManager("spell_check", max_size=5000)
      cache.set("hello", {"suggestions": ["hallo"]})
      result = cache.get("hello")  # → {"suggestions": ["hallo"]}
    """

    def __init__(self, name: str, max_size: int = 5000):
        """
        Args:
            name:      ชื่อ cache (ใช้แสดงใน log)
            max_size:  จำนวน entry สูงสุดก่อนจะ evict
        """
        self.name = name
        self.max_size = max_size
        self._store: dict = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """ดึงค่าจาก cache (thread-safe) — คืน None ถ้าไม่มี"""
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        """บันทึกค่าลง cache (thread-safe) — evict ถ้าเกิน max_size"""
        with self._lock:
            self._store[key] = value
            # ถ้า cache เกินขนาด → ลบครึ่งแรก (entries เก่าสุด)
            if len(self._store) > self.max_size:
                keys_to_delete = list(self._store.keys())[: self.max_size // 2]
                for k in keys_to_delete:
                    del self._store[k]

    def clear(self) -> None:
        """ล้าง cache ทั้งหมด (thread-safe)"""
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        """จำนวน entries ปัจจุบันใน cache"""
        with self._lock:
            return len(self._store)


# =============================================================================
# Cache Instances สำหรับแต่ละประเภท
# =============================================================================

# Cache สำหรับตรวจว่าคำอยู่ใน dictionary หรือไม่
word_check_cache = CacheManager("word_check", max_size=10000)

# Cache สำหรับผลลัพธ์ spell check (suggestions)
spell_check_cache = CacheManager("spell_check", max_size=5000)

# Cache สำหรับผลการตรวจ language mistake
lang_mistake_cache = CacheManager("lang_mistake", max_size=10000)

# Cache สำหรับ English word existence check
en_word_cache = CacheManager("en_word", max_size=10000)


# =============================================================================
# Periodic Cleanup (ล้าง cache อัตโนมัติทุก 3 นาที)
# =============================================================================

def start_periodic_cleanup(interval_seconds: int = 180) -> None:
    """
    เริ่ม background thread ที่ล้าง cache ทุก N วินาที
    ทำให้ memory ไม่บวมเกินไปเมื่อใช้งานนาน
    
    Args:
        interval_seconds: ระยะเวลาระหว่างรอบ cleanup (default: 180 = 3 นาที)
    """
    def _cleanup_loop():
        while True:
            time.sleep(interval_seconds)
            try:
                sizes = {
                    "spell": spell_check_cache.size(),
                    "word": word_check_cache.size(),
                    "lang": lang_mistake_cache.size(),
                    "en": en_word_cache.size(),
                }
                total = sum(sizes.values())

                # ล้าง cache ทั้งหมด
                spell_check_cache.clear()
                word_check_cache.clear()
                lang_mistake_cache.clear()
                en_word_cache.clear()

                print(
                    f"[INFO] Cache cleanup: cleared {total} entries "
                    f"(spell:{sizes['spell']}, word:{sizes['word']}, "
                    f"lang:{sizes['lang']}, en:{sizes['en']})"
                )
            except Exception as e:
                print(f"[ERROR] Cache cleanup failed: {e}")

    thread = threading.Thread(target=_cleanup_loop, daemon=True)
    thread.start()
