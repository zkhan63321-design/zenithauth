// c:\Users\USER\Downloads\ZSAUTH\static\js\app.js

const sdkTemplates = {
  "csharp": `// ZSAuth C# .NET SDK
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ZSAuthClient {
    class Program {
        static readonly string API_ENDPOINT = "http://localhost:5000/api/v1";
        static readonly string APP_ID = "APP-ZS-COVER-01";
        static readonly string SECRET = "zsauth_secret_key_prod";

        static async Task Main(string[] args) {
            Console.WriteLine("[*] Connecting to ZSAuth Cloud Sentinel...");
            using var client = new HttpClient();

            // 1. Initialize Session
            var initPayload = new { app_id = APP_ID, secret_key = SECRET, version = "1.0" };
            var initContent = new StringContent(JsonSerializer.Serialize(initPayload), Encoding.UTF8, "application/json");
            var initResp = await client.PostAsync($"{API_ENDPOINT}/init", initContent);
            var initJson = JsonDocument.Parse(await initResp.Content.ReadAsStringAsync());
            string token = initJson.RootElement.GetProperty("session_token").GetString();
            Console.WriteLine($"[+] Session Established: {token}");

            // 2. User Authentication with HWID Lock
            var loginPayload = new { session_token = token, username = "aurora_user_1", password = "password123", hwid = "HWID-WIN-9082A" };
            var loginContent = new StringContent(JsonSerializer.Serialize(loginPayload), Encoding.UTF8, "application/json");
            var loginResp = await client.PostAsync($"{API_ENDPOINT}/login", loginContent);
            Console.WriteLine($"[+] Authentication Status: {loginResp.StatusCode}");
        }
    }
}`,

  "cpp": `// ZSAuth C++ Native Kernel/App Client
#include <iostream>
#include <string>
#include <windows.h>
#include <wininet.h>
#pragma comment(lib, "wininet.lib")

const std::string APP_ID = "APP-ZS-COVER-01";
const std::string APP_SECRET = "zsauth_secret_key_prod";
const std::string VERSION = "1.0";

bool InitializeAuth(std::string& outToken) {
    std::cout << "[*] Authenticating with ZSAuth Cloud Engine..." << std::endl;
    // WinINet HTTPS POST to /api/v1/init
    outToken = "AUTH_SESS_SECURE_TOKEN_9082";
    return true;
}

int main() {
    std::string sessionToken;
    if (InitializeAuth(sessionToken)) {
        std::cout << "[+] Protected Application Launched! Session: " << sessionToken << std::endl;
    }
    return 0;
}`,

  "python": `# ZSAuth Python 3 Production Client
import requests
import hashlib
import platform

API_URL = "http://localhost:5000/api/v1"
APP_ID = "APP-CE8F7D4F"
SECRET = "c7fc4f642dd14e52a01f96c7"
VERSION = "1.0"

def get_hwid():
    raw = f"{platform.node()}-{platform.processor()}"
    return f"HWID-{hashlib.sha256(raw.encode()).hexdigest()[:16].upper()}"

def main():
    print("[*] Contacting ZSAuth Cloud Gateway...")
    
    # 1. Init
    init_res = requests.post(f"{API_URL}/init", json={
        "app_id": APP_ID,
        "secret_key": SECRET,
        "version": VERSION
    }).json()
    
    session_token = init_res.get("session_token")
    print(f"[+] Initialized: {init_res.get('app_name')} | Session: {session_token}")

    # 2. Login
    login_res = requests.post(f"{API_URL}/login", json={
        "session_token": session_token,
        "username": "aurora_user_1",
        "password": "password123",
        "hwid": get_hwid()
    }).json()

    print(f"[+] Login Result: {login_res.get('message')}")

if __name__ == "__main__":
    main()`,

  "javascript": `// ZSAuth Node.js Client
const axios = require('axios');

const API_URL = 'http://localhost:5000/api/v1';
const APP_ID = 'APP-ZS-COVER-01';
const SECRET_KEY = 'zsauth_secret_key_prod';

async function authenticate() {
  try {
    const initRes = await axios.post(\`\${API_URL}/init\`, {
      app_id: APP_ID,
      secret_key: SECRET_KEY,
      version: '1.0'
    });
    const token = initRes.data.session_token;
    console.log('[+] Session established:', token);

    const loginRes = await axios.post(\`\${API_URL}/login\`, {
      session_token: token,
      username: 'aurora_user_1',
      password: 'password123',
      hwid: 'NODE-HWID-90812'
    });
    console.log('[+] Auth response:', loginRes.data);
  } catch (err) {
    console.error('[-] Error:', err.response ? err.response.data : err.message);
  }
}
authenticate();`,

  "typescript": `// ZSAuth TypeScript Client
import axios, { AxiosResponse } from 'axios';

interface InitResponse {
  status: string;
  session_token: string;
  app_name: string;
}

const API_BASE = 'http://localhost:5000/api/v1';

export class ZSAuth {
  private sessionToken: string = '';

  async init(appId: string, secretKey: string, version: string = '1.0'): Promise<boolean> {
    const res: AxiosResponse<InitResponse> = await axios.post(\`\${API_BASE}/init\`, {
      app_id: appId,
      secret_key: secretKey,
      version
    });
    this.sessionToken = res.data.session_token;
    return res.data.status === 'success';
  }
}`,

  "rust": `// ZSAuth Rust Client
use reqwest::Client;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::new();
    let api_url = "http://localhost:5000/api/v1";

    println!("[*] Initializing ZSAuth Rust Native Client...");
    let init_res = client.post(format!("{}/init", api_url))
        .json(&json!({
            "app_id": "APP-ZS-COVER-01",
            "secret_key": "zsauth_secret_key_prod",
            "version": "1.0"
        }))
        .send().await?
        .json::<serde_json::Value>().await?;

    let token = init_res["session_token"].as_str().unwrap();
    println!("[+] Session token: {}", token);
    Ok(())
}`,

  "go": `// ZSAuth Golang Client
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

func main() {
	apiUrl := "http://localhost:5000/api/v1/init"
	payload, _ := json.Marshal(map[string]string{
		"app_id": "APP-ZS-COVER-01",
		"secret_key": "zsauth_secret_key_prod",
		"version": "1.0",
	})

	resp, err := http.Post(apiUrl, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	fmt.Printf("[+] ZSAuth Connected with status %s\\n", resp.Status)
}`,

  "java": `// ZSAuth Java SDK
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class ZSAuth {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        String jsonPayload = "{\\"app_id\\":\\"APP-ZS-COVER-01\\",\\"secret_key\\":\\"zsauth_secret_key_prod\\",\\"version\\":\\"1.0\\"}";
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("http://localhost:5000/api/v1/init"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
            .build();
            
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("[+] Java Auth Response: " + response.body());
    }
}`,

  "php": `<?php
// ZSAuth PHP SDK
$apiUrl = "http://localhost:5000/api/v1/init";
$data = [
    "app_id" => "APP-ZS-COVER-01",
    "secret_key" => "zsauth_secret_key_prod",
    "version" => "1.0"
];

$ch = curl_init($apiUrl);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type:application/json']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$result = curl_exec($ch);
curl_close($ch);
echo "[+] ZSAuth PHP Init: " . $result;
?>`,

  "vbnet": `' ZSAuth VB.NET Client
Imports System.Net.Http
Module Program
    Sub Main()
        Console.WriteLine("[*] ZSAuth VB.Net initialized")
    End Sub
End Module`,

  "ruby": `# ZSAuth Ruby Client
require 'net/http'
require 'json'
require 'uri'

uri = URI.parse("http://localhost:5000/api/v1/init")
header = {'Content-Type': 'application/json'}
payload = { app_id: 'APP-ZS-COVER-01', secret_key: 'zsauth_secret_key_prod', version: '1.0' }

http = Net::HTTP.new(uri.host, uri.port)
req = Net::HTTP::Post.new(uri.request_uri, header)
req.body = payload.to_json
res = http.request(req)
puts "[+] ZSAuth Ruby Response: #{res.body}"`,

  "perl": `#!/usr/bin/perl
# ZSAuth Perl Client
use strict;
use warnings;
use LWP::UserAgent;
use JSON;

my $ua = LWP::UserAgent->new;
my $req = HTTP::Request->new(POST => 'http://localhost:5000/api/v1/init');
$req->content_type('application/json');
$req->content(encode_json({app_id => 'APP-ZS-COVER-01', secret_key => 'secret', version => '1.0'}));
my $res = $ua->request($req);
print "[+] ZSAuth Perl Init: " . $res->status_line . "\n";`,

  "lua": `-- ZSAuth Lua Client
local http = require("socket.http")
print("[*] ZSAuth Lua integration module ready.")`
};

function selectSdkTab(langKey) {
  document.querySelectorAll('.sdk-tab-btn').forEach(btn => {
    if (btn.dataset.lang === langKey) {
      btn.classList.add('bg-purple-600', 'text-white');
      btn.classList.remove('text-gray-400', 'hover:text-gray-200');
    } else {
      btn.classList.remove('bg-purple-600', 'text-white');
      btn.classList.add('text-gray-400', 'hover:text-gray-200');
    }
  });

  const codeEl = document.getElementById('sdk-code-display');
  if (codeEl && sdkTemplates[langKey]) {
    codeEl.textContent = sdkTemplates[langKey];
  }
}

function showToast(message) {
  let toast = document.getElementById('toast-notification');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-notification';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span class="inline-block w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping"></span> <span>${message}</span>`;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

function copyToClipboard(text, btnElement) {
  navigator.clipboard.writeText(text).then(() => {
    showToast("Copied to clipboard!");
    if (btnElement) {
      const orig = btnElement.innerText;
      btnElement.innerText = "Copied!";
      setTimeout(() => { btnElement.innerText = orig; }, 1500);
    }
  });
}

function setupPricingToggle() {
  const toggle = document.getElementById('pricing-toggle-checkbox');
  if (!toggle) return;

  const devPrice = document.getElementById('price-dev');
  const sellerPrice = document.getElementById('price-seller');

  toggle.addEventListener('change', function() {
    if (this.checked) {
      if (devPrice) devPrice.innerHTML = "₹31.2<span class='text-sm text-gray-400 font-medium'>/mo</span>";
      if (sellerPrice) sellerPrice.innerHTML = "₹125.4<span class='text-sm text-gray-400 font-medium'>/mo</span>";
    } else {
      if (devPrice) devPrice.innerHTML = "₹49.5<span class='text-sm text-gray-400 font-medium'>/mo</span>";
      if (sellerPrice) sellerPrice.innerHTML = "₹199<span class='text-sm text-gray-400 font-medium'>/mo</span>";
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  setupPricingToggle();
  selectSdkTab('csharp');
});
