import { Parser } from 'sql-ddl-to-json-schema'

/* Code */
import code_py from '../../../data/example.py'
import code_php from '../../../data/example.php'
import code_R from '../../../data/example.R'
import code_schema from '../../../data/schema.sql'


/* Highlight */
import hljs from 'highlight.js/lib/core';

import sql from 'highlight.js/lib/languages/sql';
hljs.registerLanguage('sql', sql);

import python from 'highlight.js/lib/languages/python';
hljs.registerLanguage('python', python);

import php from 'highlight.js/lib/languages/php';
hljs.registerLanguage('php', php);

import r from 'highlight.js/lib/languages/r';
hljs.registerLanguage('r', r);


/* Code examples [HTML] */
const examples = () => {
  return {
    'PHP': hljs.highlight(code_php, {language: 'php', ignoreIllegals: true }).value,
    'Python': hljs.highlight(code_py, {language: 'python', ignoreIllegals: true }).value,
    'R': hljs.highlight(code_R, {language: 'r', ignoreIllegals: true }).value
  };
};

const schema = () => {
  const parser = new Parser('mysql');
  let mysql_dialect = code_schema
    .replaceAll('"', '')
    .replaceAll('AUTOINCREMENT', 'AUTO_INCREMENT')
    .replaceAll(', -- ', ' COMMENT ')
    .replaceAll(' -- ', ' COMMENT ');
  
  return {
    'compact': parser.feed(mysql_dialect).toCompactJson(parser.results),
    'documents': JSON.stringify(parser.feed(mysql_dialect).toJsonSchemaArray()),
    'hl.sqlite': hljs.highlight(code_schema, {language: 'sql', ignoreIllegals: true }).value,
    'sqlite': mysql_dialect
  }
}

const download = (name, content, mime = 'application/json') => {
  let e = document.createElement('a');
  e.setAttribute('href','data:' + mime + ';charset=utf-8, ' + encodeURIComponent(content));
  e.setAttribute('download', name);
  document.body.appendChild(e);
  e.click();
  document.body.removeChild(e);
}

export { examples, schema, download };
