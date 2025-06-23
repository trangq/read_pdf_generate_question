# 📄🧠 Tạo Câu Hỏi Trắc Nghiệm từ PDF với Gemini AI

Ứng dụng Streamlit giúp bạn **tự động tạo bộ câu hỏi trắc nghiệm từ nội dung PDF** bằng công nghệ Google Gemini AI.  
Bạn có thể tải lên tài liệu, tạo câu hỏi, làm bài và nhận kết quả ngay lập tức!


---

## 🚀 Trải nghiệm ngay

🌐 Ứng dụng:  https://readpdfgeneratequestion.streamlit.app/
📦 Mã nguồn: [GitHub - trangq/read_pdf_generate_question](https://github.com/trangq/read_pdf_generate_question)

---

## 🧩 Tính năng

- 📤 TNhập google api key + tải lên file PDF
- 🤖 Trích xuất nội dung & sinh câu hỏi bằng Google Gemini AI
- ✅ Làm bài trắc nghiệm và chấm điểm tự động
- 🕒 Hiển thị thời gian làm bài
- 🔐 Cho phép người dùng nhập API Key riêng (bảo mật hơn)

---

## 🛠️ Cài đặt (local)

```bash
git clone https://github.com/trangq/read_pdf_generate_question.git
cd read_pdf_generate_question
pip install -r requirements.txt
streamlit run app.py
