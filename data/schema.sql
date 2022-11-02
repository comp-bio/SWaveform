CREATE TABLE IF NOT EXISTS "target" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, -- 'Primary ID',
  "name" text(255) NOT NULL, -- 'Sample name in VCF file',
  "file" text(255) NOT NULL, -- '.cram or .bam file suffix',
  "dataset" text(255) NOT NULL, -- 'Name of source database',
  "genome_version" text(255), -- 'Genome version (for karyotype)',
  "population" text(255) NULL, -- 'Population name',
  "region" text(255) NULL, -- 'Population region',
  "sex" text(255) NULL, -- 'Sex',
  "meancov" float NULL -- 'Average genome coverage for a Sample'
);

CREATE TABLE IF NOT EXISTS "signal" (
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, -- 'Primary ID',
  "target_id" integer NOT NULL, -- 'Reference for target primary ID',
  "chr" text(128) NOT NULL, -- 'Chromosome',
  "start" integer NOT NULL, -- 'Signal start coordinate (-256bp from bp)',
  "end" integer NOT NULL, -- 'End of signal coordinate (+ 256bp from bp)',
  "type" text(128) NOT NULL, -- 'Structural variation Type',
  "side" text(32) NOT NULL, -- 'Left, right or default breakpoint of the SV (L, R, BP)',
  "size" integer NOT NULL, -- 'SV size (Distance between breakpoints)',
  "genotype" integer NOT NULL, -- 'Genotype (1 for 1/0, 2 for 1/1)',
  "coverage_offset" integer NOT NULL, -- 'Coverage offset (for ext. binary file)',
  FOREIGN KEY ("target_id") REFERENCES "target" ("id")
);

CREATE INDEX IF NOT EXISTS "sig_target_id" ON "signal" ("target_id");
CREATE INDEX IF NOT EXISTS "sig_chr" ON "signal" ("chr");
CREATE INDEX IF NOT EXISTS "sig_start" ON "signal" ("start");
CREATE INDEX IF NOT EXISTS "sig_end" ON "signal" ("end");
CREATE INDEX IF NOT EXISTS "sig_type" ON "signal" ("type");
CREATE INDEX IF NOT EXISTS "sig_side" ON "signal" ("side");
CREATE INDEX IF NOT EXISTS "sig_size" ON "signal" ("size");
CREATE INDEX IF NOT EXISTS "sig_genotype" ON "signal" ("genotype");
