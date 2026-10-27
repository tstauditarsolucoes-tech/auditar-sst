import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,symlink,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {inventory} from './inventory-legacy-backup.mjs';
test('inventario privado exige pasta propria, ignora symlinks e nao retorna nomes',async()=>{
  await assert.rejects(inventory('/'),/Caminho negado/);
  const dir=await mkdtemp(join(tmpdir(),'auditar-sst-backup-ci-'));
  try{
    await writeFile(join(dir,'fic1.csv'),'somente dado de teste');
    await writeFile(join(dir,'fic2.csv'),'somente dado de teste');
    await symlink('/etc/passwd',join(dir,'link.txt'));
    const output=await inventory(dir);
    assert.equal(output.files,2);
    assert.equal(output.skippedSymlinks,1);
    assert.equal(output.duplicateCount,1);
    assert.ok(output.byType['.csv'].bytes>0);
    assert.ok(!JSON.stringify(output).includes('fic1'));
    assert.ok(!JSON.stringify(output).includes('passwd'));
  }finally{await rm(dir,{recursive:true,force:true});}
});
