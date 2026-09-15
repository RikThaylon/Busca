"""Isolated, bounded document extraction. No macros, URLs, shell or images are executed."""
import io
import json
import re
import sys


def extract(raw, extension):
    if extension == '.pdf':
        if not raw.startswith(b'%PDF-'):
            raise ValueError('Assinatura PDF inválida')
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted or len(reader.pages) > 100:
            raise ValueError('PDF protegido ou acima de 100 páginas')
        root = reader.trailer['/Root']
        if any(k in root for k in ['/OpenAction', '/AA']) or '/JavaScript' in root.get('/Names', {}):
            raise ValueError('PDF com ações ativas não permitido')
        pages = [p.extract_text() or '' for p in reader.pages]
    else:
        if b'\x00' in raw:
            raise ValueError('Texto inválido')
        pages = raw.decode('utf-8-sig').split('\f')
    if len(pages) > 100 or sum(map(len, pages)) > 400_000:
        raise ValueError('Limite de extração excedido')
    chunks = []
    for number, page in enumerate(pages, 1):
        page = page.strip()
        if not page:
            continue
        section = page.splitlines()[0][:120]
        # Paragraph boundaries preserve rules, numbers and qualifiers together.
        for paragraph in re.split(r'\n\s*\n', page):
            paragraph = paragraph.strip()
            if len(paragraph) < 25:
                continue
            buffer = ''
            for sentence in re.split(r'(?<=[.!?])\s+', paragraph):
                if len(sentence) > 1200:
                    raise ValueError('Trecho longo demais sem limites de frase; revise a extração')
                if buffer and len(buffer) + len(sentence) + 1 > 1200:
                    chunks.append({'page': number, 'section': section, 'body': buffer})
                    buffer = ''
                buffer = (buffer + ' ' + sentence).strip()
            if buffer:
                chunks.append({'page': number, 'section': section, 'body': buffer})
    if not chunks:
        raise ValueError('Documento sem texto pesquisável; OCR não incluído neste piloto')
    return {'pages': len(pages), 'chunks': chunks}


if __name__ == '__main__':
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    try:
        print(json.dumps(extract(sys.stdin.buffer.read(10 * 1024 * 1024 + 1), sys.argv[1])))
    except Exception:
        print(json.dumps({'error': 'Não foi possível extrair texto. Use PDF textual sem ações ativas (até 100 páginas) ou TXT UTF-8.'}))
        sys.exit(1)
