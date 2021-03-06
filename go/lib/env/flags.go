// Copyright 2018 Anapaya Systems
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package env

import (
	"flag"
	"fmt"
	"os"

	"github.com/scionproto/scion/go/lib/config"
	"github.com/scionproto/scion/go/lib/sock/reliable"
)

var (
	configFile string
	helpConfig bool
	version    bool
	dispatcher string
)

// AddFlags adds the config and sample flags.
func AddFlags() {
	flag.StringVar(&configFile, "config", "", "TOML config file.")
	flag.BoolVar(&helpConfig, "help-config", false, "Output sample commented config file.")
	flag.BoolVar(&version, "version", false, "Output version information and exit.")
	flag.StringVar(&dispatcher, "dispatcher", reliable.DefaultDispPath, "Path to dispatcher socket")
}

// Dispatcher returns the dispatcher socket path passed through the flag.
func Dispatcher() string {
	return dispatcher
}

// ConfigFile returns the config file path passed through the flag.
func ConfigFile() string {
	return configFile
}

// Usage outputs run-time help to stdout.
func Usage() {
	fmt.Printf("Usage: %s -config <FILE> \n   or: %s -help-config\n\nArguments:\n",
		os.Args[0], os.Args[0])
	flag.CommandLine.SetOutput(os.Stdout)
	flag.PrintDefaults()
}

// CheckFlags checks whether the config or help-config flags have been set. In case the
// help-config flag is set, the config flag is ignored and a commented sample config
// is written to stdout.
//
// The first return value is the return code of the program. The second value
// indicates whether the program can continue with its execution or should exit.
func CheckFlags(sampler config.Sampler) (int, bool) {
	if helpConfig {
		sampler.Sample(os.Stdout, nil, nil)
		return 0, false
	}
	if version {
		fmt.Printf(VersionInfo())
		return 0, false
	}
	if configFile == "" {
		fmt.Fprintln(os.Stderr, "Err: Missing config file")
		flag.Usage()
		return 1, false
	}
	return 0, true
}
