CREATE TABLE IF NOT EXISTS "target" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "name" text(255) NOT NULL,
  "file" text(255) NOT NULL,
  "dataset" text(255) NOT NULL,
  "genome_version" text(255),
  "population" text(255) NULL,
  "region" text(255) NULL,
  "sex" text(255) NULL,
  "meancov" real NULL
);

CREATE TABLE IF NOT EXISTS "signal" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "target_id" integer NOT NULL,
  "chr" text(128) NOT NULL,
  "start" integer NOT NULL,
  "end" integer NOT NULL,
  "type" text(128) NOT NULL,
  "side" text(32) NOT NULL,
  "genotype" integer NOT NULL,
  "coverage" blob NOT NULL,
  FOREIGN KEY ("target_id") REFERENCES "target" ("id")
);

CREATE INDEX IF NOT EXISTS "sig_target_id" ON "signal" ("target_id");
CREATE INDEX IF NOT EXISTS "sig_chr" ON "signal" ("chr");
CREATE INDEX IF NOT EXISTS "sig_start" ON "signal" ("start");
CREATE INDEX IF NOT EXISTS "sig_end" ON "signal" ("end");
CREATE INDEX IF NOT EXISTS "sig_type" ON "signal" ("type");
CREATE INDEX IF NOT EXISTS "sig_side" ON "signal" ("side");
CREATE INDEX IF NOT EXISTS "sig_genotype" ON "signal" ("genotype");
