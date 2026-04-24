/**
 * content.js — P.L.I.C.K. Content Script (Main Entry Point)
 *
 * ไฟล์นี้เป็น entry point หลักของ extension ที่ทำงานในทุกหน้าเว็บ
 * มีหน้าที่แค่ตามหา Input/Textarea และ ContentEditable เดิมและใหม่
 * เพื่อสั่งให้ Handler ต่างๆ เข้ามาทำงาน
 */

/**
 * หา input/textarea/contentEditable ทั้งหมดในหน้าเว็บ แล้วเพิ่ม listeners
 * ใช้ flag _plAttached ป้องกันการ attach ซ้ำ
 */
function setupAll() {
  // input[type='text'] และ textarea
  document.querySelectorAll("input[type='text'], textarea").forEach(el => {
    if (!el._plAttached) {
      attach(el); // มาจาก auto/input-handler.js
      el._plAttached = true;
      el.setAttribute("spellcheck", "false"); // ปิด native spellcheck
    }
  });

  // contentEditable elements
  document.querySelectorAll("[contenteditable='true']").forEach(el => {
    if (!el._plAttached) {
      attachContentEditable(el); // มาจาก auto/editable-handler.js
      el._plAttached = true;
      el.setAttribute("spellcheck", "false");
    }
  });
}

// ── เริ่มระบบ ──
// โหลดการตั้งค่าก่อนเป็นอย่างแรก เมื่อพร้อมก็ให้ลุยเลย
loadSettings(() => {
  setupAll();
  
  // MutationObserver: คอยส่องดูว่ามีช่องกรอกข้อความใหม่โผล่ขึ้นมาทีหลังไหม (เพื่อรองรับเว็บยุคใหม่แบบ SPA)
  new MutationObserver(setupAll).observe(document.body, {
    childList: true,
    subtree: true,
  });
});