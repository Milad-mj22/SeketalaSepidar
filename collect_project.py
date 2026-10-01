import os


def collect_py_files(root_dir, output_file="collected_py_files.txt"):
    """
    پوشه ریشه رو می‌گیره و از کاربر فقط برای پوشه‌های سطح بالا می‌پرسه.
    اگه y بزنی: اون پوشه + همه زیرپوشه‌هاش انتخاب میشن.
    اگه n بزنی: اون پوشه + همه زیرپوشه‌هاش نادیده گرفته میشن.
    اگه q بزنی: کل عملیات لغو میشه.
    """
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        print(f"❌ مسیر وارد شده معتبر نیست: {root_dir}")
        return

    # پیدا کردن فقط پوشه‌های سطح اول (زیرپوشه‌های مستقیم ریشه + خود ریشه)
    try:
        entries = sorted(os.listdir(root_dir))
    except Exception as e:
        print(f"❌ خطا در خواندن پوشه: {e}")
        return

    top_level_dirs = [root_dir]  # خود پوشه ریشه
    for name in entries:
        full_path = os.path.join(root_dir, name)
        if os.path.isdir(full_path):
            top_level_dirs.append(full_path)

    # انتخاب پوشه‌ها
    selected_dirs = set()
    print("\n=== انتخاب پوشه‌ها ===")
    print("برای هر پوشه یکی از گزینه‌ها رو وارد کن:")
    print("  y = بله (این پوشه + همه زیرپوشه‌هاش استخراج بشن)")
    print("  n = خیر (این پوشه + همه زیرپوشه‌هاش نادیده گرفته بشن)")
    print("  q = لغو کل عملیات\n")

    for d in top_level_dirs:
        rel = os.path.relpath(d, root_dir)
        if rel == ".":
            rel = "(پوشه اصلی - خود ریشه)"
        while True:
            answer = input(f"استخراج از «{rel}»؟ [y/n/q]: ").strip().lower()
            if answer == "y":
                selected_dirs.add(d)
                break
            elif answer == "n":
                break
            elif answer == "q":
                print("⛔ عملیات لغو شد.")
                return
            else:
                print("لطفاً یکی از y / n / q رو وارد کن.")

    if not selected_dirs:
        print("⚠️ هیچ پوشه‌ای برای استخراج انتخاب نشد.")
        return

    # جمع‌آوری همه فایل‌های .py از پوشه‌های انتخاب‌شده (و همه زیرپوشه‌هاشون)
    collected_files = set()
    for d in sorted(selected_dirs):
        for current_dir, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith(".py"):
                    collected_files.add(os.path.join(current_dir, f))

    collected_files = sorted(collected_files)

    if not collected_files:
        print("⚠️ هیچ فایل .py پیدا نشد.")
        return

    # نوشتن در فایل خروجی
    out_path = os.path.join(root_dir, output_file)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(f"# مجموع فایل‌های .py استخراج شده: {len(collected_files)}\n")
        out.write(f"# پوشه ریشه: {root_dir}\n")
        out.write("=" * 80 + "\n\n")

        for file_path in collected_files:
            out.write("=" * 80 + "\n")
            out.write(f"# مسیر فایل: {file_path}\n")
            out.write(f"# پوشه: {os.path.dirname(file_path)}\n")
            out.write("=" * 80 + "\n")
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                out.write(content)
                if not content.endswith("\n"):
                    out.write("\n")
            except Exception as e:
                out.write(f"⚠️ خطا در خواندن فایل: {e}\n")
            out.write("\n\n")

    print(f"\n✅ تمام شد! {len(collected_files)} فایل .py در این مسیر ذخیره شد:")
    print(f"   {out_path}")


if __name__ == "__main__":
    root = input("مسیر پوشه ریشه رو وارد کن: ").strip().strip('"').strip("'")
    collect_py_files(root)