LEGACY_SELECTION_FIELDS = ("check_measure", "remove_product", "split_shipping")


def _is_character_column(cr, table_name, column_name):
    cr.execute(
        """
        SELECT data_type
          FROM information_schema.columns
         WHERE table_name = %s
           AND column_name = %s
        """,
        (table_name, column_name),
    )
    row = cr.fetchone()
    return bool(row and row[0] in {"character varying", "text"})


def migrate(cr, version):
    for field_name in LEGACY_SELECTION_FIELDS:
        legacy_column = f"x_legacy_{field_name}"
        if _is_character_column(cr, "sale_order", field_name):
            cr.execute(f'ALTER TABLE sale_order RENAME COLUMN "{field_name}" TO "{legacy_column}"')
