import { MeshWallet } from "@meshsdk/core";
import fs from "node:fs";
import * as path from 'path';

async function main() {

  const keysDir  = "keys";
  const skPath   = path.join(keysDir, "me.sk");
  const addrPath = path.join(keysDir, "me.addr");

  if (fs.existsSync(skPath)) {
    console.log(`abort! found an existing secret key ${skPath}`)
    return;
  }

  fs.mkdirSync(keysDir);

  const secret_key = MeshWallet.brew(true) as string;

  fs.writeFileSync(skPath, secret_key);
  console.log(`generated ${skPath}`);

  const wallet = new MeshWallet({
    networkId: 0,
    key: {
      type: "root",
      bech32: secret_key,
    },
  });

  fs.writeFileSync(addrPath, (await wallet.getUnusedAddresses())[0]);
  console.log(`generated ${addrPath}`);
}

main();
