doc:
	doxygen Doxyfile

clean:
	rm -f doxygen_sqlite3.db
	rm -rf html
	rm -rf latex

.PHONY: doc clean
