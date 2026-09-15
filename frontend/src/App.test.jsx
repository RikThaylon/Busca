// @vitest-environment jsdom
import React from 'react';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import {cleanup, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {App} from './main';

const evidence={chunk_id:'c1',document_id:'d1',document:'Compras.txt',page:2,section:'Alçadas',excerpt:'O gerente e o diretor financeiro aprovam compras superiores a R$ 10.000.'};
let found=true;
let turn=0;
beforeEach(()=>{
  found=true;turn=0;
  Element.prototype.scrollIntoView=vi.fn();
  HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  HTMLDialogElement.prototype.close=function(){this.open=false;};
  vi.stubGlobal('fetch',vi.fn(async(url,options={})=>{
    const data={
      '/api/config':{demo:true,search:'textual demonstrativa',retention_days:30},
      '/api/me':{email:'teste@local',role:'admin',tenant:'Empresa fictícia'},
      '/api/documents':[],
      '/api/history':[],
      '/api/chat':{id:`h${url==='/api/chat'?++turn:turn}`,answer:found?evidence.excerpt:'NÃO ENCONTREI EVIDÊNCIA SUFICIENTE',found,sources:found?[evidence]:[],elapsed_ms:25},
      '/api/documents/d1/source?page=2':{document:'Compras.txt',page:2,pages:2,chunks:[{id:'c1',text:evidence.excerpt,section:'Alçadas'}]},
    }[url];
    return {ok:true,json:async()=>data};
  }));
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

test('demo question opens its page evidence and preserves follow-up context',async()=>{
  const user=userEvent.setup();
  render(<App/>);
  await user.click(await screen.findByRole('button',{name:/Quem aprova compras superiores/}));
  await screen.findByText('FONTES UTILIZADAS');
  const source=screen.getByRole('button',{name:/Abrir Compras.txt, página 2/});
  await user.click(source);
  await screen.findByText('Página 2 de 2');
  expect(screen.getByRole('link',{name:/Baixar original/}).getAttribute('href')).toBe('/api/documents/d1/download');
  await user.click(screen.getByRole('button',{name:'Fechar fonte'}));
  await user.click(screen.getByRole('button',{name:/E onde está escrito isso/}));
  await waitFor(()=>expect(fetch).toHaveBeenCalledWith('/api/chat',expect.objectContaining({body:JSON.stringify({question:'E onde está escrito isso?',previous_id:'h1'})})));
});

test('no evidence remains explicit and never renders a source',async()=>{
  found=false;
  const user=userEvent.setup();
  render(<App/>);
  expect(await screen.findByText('DADOS FICTÍCIOS — AMBIENTE DEMONSTRATIVO')).toBeTruthy();
  await user.type(screen.getByLabelText('Sua pergunta'),'Qual é a senha?');
  await user.click(screen.getByRole('button',{name:'Enviar pergunta'}));
  await screen.findByText('NÃO ENCONTREI EVIDÊNCIA SUFICIENTE');
  expect(screen.queryByText('FONTES UTILIZADAS')).toBeNull();
});
