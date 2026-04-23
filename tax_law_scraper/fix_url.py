"""
修复数据库中已有的 detail_url，将 www.chinatax.gov.cn 替换为 fgk.chinatax.gov.cn
"""
import sqlite3
from config.settings import DB_PATH


def fix_detail_urls():
    """修复 detail_url 中的域名"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 查找需要修复的记录
    cursor.execute("""
        SELECT id, detail_url FROM tax_documents
        WHERE detail_url LIKE '%www.chinatax.gov.cn%'
    """)

    rows = cursor.fetchall()
    print(f"找到 {len(rows)} 条需要修复的记录")

    if not rows:
        print("没有需要修复的记录")
        conn.close()
        return

    # 更新记录
    updated_count = 0
    for row in rows:
        doc_id = row[0]
        old_url = row[1]
        new_url = old_url.replace('www.chinatax.gov.cn', 'fgk.chinatax.gov.cn')

        cursor.execute("""
            UPDATE tax_documents
            SET detail_url = ?
            WHERE id = ?
        """, (new_url, doc_id))
        updated_count += 1

    conn.commit()
    conn.close()

    print(f"成功修复 {updated_count} 条记录")


if __name__ == "__main__":
    fix_detail_urls()
