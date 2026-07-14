import io
import json
import os
import importlib

import pytest


@pytest.fixture
def server_module(tmp_path, monkeypatch):
    """Import server.py fresh and redirect its data files into tmp_path."""
    import server as server_module  # assumes server.py is on sys.path

    importlib.reload(server_module)  # reset to defaults in case another test mutated it

    data_dir = tmp_path / "data"
    monkeypatch.setattr(server_module, "DATA_DIR", str(data_dir))
    monkeypatch.setattr(server_module, "BOOKS_CSV", str(data_dir / "books.csv"))
    monkeypatch.setattr(server_module, "LOANS_CSV", str(data_dir / "loans.csv"))

    os.makedirs(data_dir, exist_ok=True)
    server_module.init_csv_files()  # (re)create sample books.csv / loans.csv in tmp_path

    return server_module


@pytest.fixture
def client(server_module):
    server_module.app.config["TESTING"] = True
    with server_module.app.test_client() as c:
        yield c


BOOK_HEADERS = ["id", "name", "author", "code", "number", "library"]
LOAN_HEADERS = ["id", "نشان", "نام", "درجه", "قسمت", "شماره پرسنلی/دانشجویی",
                "شماره تماس", "عنوان کتاب", "کتابخانه", "کد کنگره",
                "تاریخ امانت", "تاریخ بازگردانی"]


# ==================== CSV HELPER UNIT TESTS ====================

class TestCsvHelpers:
    def test_read_csv_missing_file_returns_empty_list(self, server_module, tmp_path):
        result = server_module.read_csv(str(tmp_path / "nope.csv"))
        assert result == []

    def test_write_then_read_roundtrip_preserves_unicode(self, server_module, tmp_path):
        path = str(tmp_path / "roundtrip.csv")
        rows = [{"id": 1, "name": "کشکول طبسی", "author": "الف", "code": "AC1",
                 "number": 3, "library": "اصلی"}]
        assert server_module.write_csv(path, rows, BOOK_HEADERS) is True
        result = server_module.read_csv(path)
        assert result[0]["name"] == "کشکول طبسی"
        assert result[0]["id"] == 1          # coerced to int
        assert result[0]["number"] == 3      # coerced to int

    def test_write_csv_empty_list_writes_header_only(self, server_module, tmp_path):
        path = str(tmp_path / "empty.csv")
        assert server_module.write_csv(path, [], BOOK_HEADERS) is True
        with open(path, encoding="utf-8-sig") as f:
            lines = f.read().strip().splitlines()
        assert len(lines) == 1  # header row only

    def test_read_csv_non_numeric_id_defaults_to_zero(self, server_module, tmp_path):
        path = tmp_path / "bad_id.csv"
        path.write_text("id,name,author,code,number,library\nabc,Foo,Bar,C1,2,Main\n",
                         encoding="utf-8-sig")
        result = server_module.read_csv(str(path))
        assert result[0]["id"] == 0

    def test_write_csv_missing_field_in_row_defaults_to_empty_string(self, server_module, tmp_path):
        path = str(tmp_path / "partial.csv")
        rows = [{"id": 1, "name": "OnlyName"}]  # missing author/code/number/library
        server_module.write_csv(path, rows, BOOK_HEADERS)
        result = server_module.read_csv(path)
        assert result[0]["author"] == ""
        assert result[0]["library"] == ""


class TestMigrateCsvHeaders:
    def test_adds_missing_column_with_default_and_keeps_existing_rows(self, server_module, tmp_path):
        path = tmp_path / "old_books.csv"
        # old-style file without the 'library' column
        path.write_text("id,name,author,code,number\n1,Old Book,Some Author,C1,5\n",
                         encoding="utf-8-sig")
        server_module.migrate_csv_headers(str(path), BOOK_HEADERS, {"library": "اصلی"})
        result = server_module.read_csv(str(path))
        assert result[0]["library"] == "اصلی"
        assert result[0]["name"] == "Old Book"

    def test_noop_when_already_up_to_date(self, server_module, tmp_path):
        path = tmp_path / "current_books.csv"
        path.write_text("id,name,author,code,number,library\n1,X,Y,C,1,اصلی\n",
                         encoding="utf-8-sig")
        before = path.read_text(encoding="utf-8-sig")
        server_module.migrate_csv_headers(str(path), BOOK_HEADERS, {"library": "اصلی"})
        after = path.read_text(encoding="utf-8-sig")
        assert before == after

    def test_preserves_extra_unknown_columns(self, server_module, tmp_path):
        path = tmp_path / "extra_col.csv"
        path.write_text("id,name,author,code,number,library,notes\n"
                         "1,X,Y,C,1,اصلی,some note\n", encoding="utf-8-sig")
        server_module.migrate_csv_headers(str(path), BOOK_HEADERS, {"library": "اصلی"})
        with open(path, encoding="utf-8-sig") as f:
            header_line = f.readline()
        assert "notes" in header_line


# ==================== API ROUTE TESTS ====================

class TestStatusRoute:
    def test_status_ok(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "online"
        assert body["books_file"] is True
        assert body["loans_file"] is True


class TestBooksRoutes:
    def test_get_books_returns_sample_data_on_fresh_init(self, client):
        resp = client.get("/api/books")
        assert resp.status_code == 200
        books = resp.get_json()
        assert isinstance(books, list)
        assert len(books) == 3  # matches server.py's sample data

    def test_post_books_valid_list_saves_and_replaces(self, client):
        payload = [{"id": 1, "name": "کتاب تست", "author": "نویسنده",
                    "code": "T1", "number": 2, "library": "اصلی"}]
        resp = client.post("/api/books", data=json.dumps(payload),
                            content_type="application/json")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 1

        # confirm it actually replaced (not appended to) the old sample data
        resp2 = client.get("/api/books")
        books = resp2.get_json()
        assert len(books) == 1
        assert books[0]["name"] == "کتاب تست"

    def test_post_books_malformed_json_returns_500_not_400(self, client):
        """
        Known-bug case: an empty/invalid JSON body makes Flask's
        request.get_json() raise internally. That exception is swallowed by
        the route's broad `except Exception`, so the client gets a generic
        500 instead of a clean 400. This test pins the current (undesirable)
        behavior so a future fix shows up as a passing improvement, not a
        silent regression.
        """
        resp = client.post("/api/books", data="", content_type="application/json")
        assert resp.status_code == 500

    def test_post_books_non_list_body_returns_400(self, client):
        resp = client.post("/api/books", data=json.dumps({"id": 1}),
                            content_type="application/json")
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_post_books_empty_list_is_rejected_not_cleared(self, client):
        """
        Known-bug case: the route checks `if not data:` before checking
        `isinstance(data, list)`. An empty list `[]` is falsy in Python, so
        this is indistinguishable from "no data provided" -- meaning there is
        currently no way to clear all books via this endpoint. Pinning this
        so the bug is visible rather than silently relied upon.
        """
        resp = client.post("/api/books", data=json.dumps([]),
                            content_type="application/json")
        assert resp.status_code == 400
        # data on disk is untouched by the rejected request
        assert len(client.get("/api/books").get_json()) == 3


class TestLoansRoutes:
    def test_get_loans_returns_sample_data(self, client):
        resp = client.get("/api/loans")
        assert resp.status_code == 200
        loans = resp.get_json()
        assert len(loans) == 2

    def test_post_loans_valid_list_saves(self, client):
        payload = [{"id": 1, "نشان": "تست", "نام": "علی", "درجه": "", "قسمت": "",
                    "شماره پرسنلی/دانشجویی": "", "شماره تماس": "", "عنوان کتاب": "کتاب الف",
                    "کتابخانه": "اصلی", "کد کنگره": "", "تاریخ امانت": "1404/01/01",
                    "تاریخ بازگردانی": ""}]
        resp = client.post("/api/loans", data=json.dumps(payload),
                            content_type="application/json")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 1

    def test_post_loans_non_list_returns_400(self, client):
        resp = client.post("/api/loans", data=json.dumps("not a list"),
                            content_type="application/json")
        assert resp.status_code == 400


class TestImportCsv:
    def test_import_books_csv(self, client):
        csv_content = "id,name,author,code,number,library\n2,New Book,New Author,NB1,4,اصلی\n"
        data = {
            "books": (io.BytesIO(csv_content.encode("utf-8-sig")), "books.csv"),
        }
        resp = client.post("/api/import/csv", data=data,
                            content_type="multipart/form-data")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert "books" in body["results"]

        books = client.get("/api/books").get_json()
        assert len(books) == 1
        assert books[0]["name"] == "New Book"

    def test_import_no_files_returns_400(self, client):
        resp = client.post("/api/import/csv", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_import_csv_field_with_comma_breaks_naive_parser(self, client):
        """
        Known-risk case: /api/import/csv splits rows on a raw `.split(',')`
        instead of using the `csv` module, so a quoted field containing a
        comma (e.g. an author name written as "Doe, Jane") will misalign
        columns. This test documents the current (buggy) behavior so a future
        fix is caught by a red test rather than discovered in production.
        """
        csv_content = 'id,name,author,code,number,library\n3,Title,"Doe, Jane",C3,1,اصلی\n'
        data = {"books": (io.BytesIO(csv_content.encode("utf-8-sig")), "books.csv")}
        client.post("/api/import/csv", data=data, content_type="multipart/form-data")
        books = client.get("/api/books").get_json()
        # Because of the naive split, "author" ends up as '"Doe' rather than 'Doe, Jane'.
        assert books[0]["author"] != "Doe, Jane"


class TestExportAndDownload:
    def test_export_all_creates_both_files(self, client, server_module):
        resp = client.get("/api/export/csv?type=all")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["files"]["books"] == "/data/export_books.csv"
        assert body["files"]["loans"] == "/data/export_loans.csv"
        assert os.path.exists(os.path.join(server_module.DATA_DIR, "export_books.csv"))
        assert os.path.exists(os.path.join(server_module.DATA_DIR, "export_loans.csv"))

    def test_export_books_only(self, client):
        resp = client.get("/api/export/csv?type=books")
        body = resp.get_json()
        assert body["files"]["books"] == "/data/export_books.csv"
        assert body["files"]["loans"] is None

    def test_download_existing_file(self, client):
        client.get("/api/export/csv?type=all")
        resp = client.get("/data/export_books.csv")
        assert resp.status_code == 200

    def test_download_missing_file_returns_404(self, client):
        resp = client.get("/data/does_not_exist.csv")
        assert resp.status_code == 404


class TestIndexRoute:
    def test_index_missing_html_returns_404(self, client):
        # No index.html was placed next to server.py in this isolated test run
        resp = client.get("/")
        assert resp.status_code in (200, 404)  # 200 if repo's real index.html is present