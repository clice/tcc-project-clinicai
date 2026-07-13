/**
 * Verifica se toda referência PERMISSIONS.X usada no frontend existe no
 * catálogo declarado em src/utils/permissions.js.
 *
 * O script não depende do ESLint nem de bibliotecas externas, portanto pode
 * ser executado antes da instalação das dependências e também na integração
 * contínua. Ele evita a regressão corrigida na RBAC-02: uma propriedade
 * inexistente resulta em undefined e pode ocultar indevidamente uma ação.
 */

import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url))
const frontendDirectory = path.resolve(scriptDirectory, '..')
const sourceDirectory = path.join(frontendDirectory, 'src')
const permissionsFile = path.join(sourceDirectory, 'utils', 'permissions.js')

const listSourceFiles = async (directory) => {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await listSourceFiles(fullPath)))
    } else if (/\.(?:js|jsx|mjs)$/.test(entry.name)) {
      files.push(fullPath)
    }
  }

  return files
}

const permissionsSource = await readFile(permissionsFile, 'utf8')
const catalogMatch = permissionsSource.match(/export const PERMISSIONS\s*=\s*\{([\s\S]*?)\n\}/)

if (!catalogMatch) {
  throw new Error('Não foi possível localizar o catálogo PERMISSIONS.')
}

const definitions = new Set(
  [...catalogMatch[1].matchAll(/^\s*([A-Z][A-Z0-9_]*)\s*:/gm)].map((match) => match[1]),
)
const undefinedReferences = []

for (const file of await listSourceFiles(sourceDirectory)) {
  const source = await readFile(file, 'utf8')
  for (const match of source.matchAll(/PERMISSIONS\.([A-Z][A-Z0-9_]*)/g)) {
    if (!definitions.has(match[1])) {
      undefinedReferences.push(`${path.relative(frontendDirectory, file)}: PERMISSIONS.${match[1]}`)
    }
  }
}

if (undefinedReferences.length > 0) {
  console.error('Foram encontradas referências de permissão não definidas:')
  for (const reference of undefinedReferences) {
    console.error(`- ${reference}`)
  }
  process.exitCode = 1
} else {
  console.log(
    `Catálogo de permissões válido: ${definitions.size} constantes definidas e nenhuma referência inválida.`,
  )
}
