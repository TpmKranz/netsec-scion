// Code generated by MockGen. DO NOT EDIT.
// Source: github.com/scionproto/scion/go/lib/snet/internal/pathsource (interfaces: PathSource)

// Package mock_pathsource is a generated GoMock package.
package mock_pathsource

import (
	context "context"
	gomock "github.com/golang/mock/gomock"
	addr "github.com/scionproto/scion/go/lib/addr"
	overlay "github.com/scionproto/scion/go/lib/overlay"
	spath "github.com/scionproto/scion/go/lib/spath"
	reflect "reflect"
)

// MockPathSource is a mock of PathSource interface
type MockPathSource struct {
	ctrl     *gomock.Controller
	recorder *MockPathSourceMockRecorder
}

// MockPathSourceMockRecorder is the mock recorder for MockPathSource
type MockPathSourceMockRecorder struct {
	mock *MockPathSource
}

// NewMockPathSource creates a new mock instance
func NewMockPathSource(ctrl *gomock.Controller) *MockPathSource {
	mock := &MockPathSource{ctrl: ctrl}
	mock.recorder = &MockPathSourceMockRecorder{mock}
	return mock
}

// EXPECT returns an object that allows the caller to indicate expected use
func (m *MockPathSource) EXPECT() *MockPathSourceMockRecorder {
	return m.recorder
}

// Get mocks base method
func (m *MockPathSource) Get(arg0 context.Context, arg1, arg2 addr.IA) (*overlay.OverlayAddr, *spath.Path, error) {
	m.ctrl.T.Helper()
	ret := m.ctrl.Call(m, "Get", arg0, arg1, arg2)
	ret0, _ := ret[0].(*overlay.OverlayAddr)
	ret1, _ := ret[1].(*spath.Path)
	ret2, _ := ret[2].(error)
	return ret0, ret1, ret2
}

// Get indicates an expected call of Get
func (mr *MockPathSourceMockRecorder) Get(arg0, arg1, arg2 interface{}) *gomock.Call {
	mr.mock.ctrl.T.Helper()
	return mr.mock.ctrl.RecordCallWithMethodType(mr.mock, "Get", reflect.TypeOf((*MockPathSource)(nil).Get), arg0, arg1, arg2)
}
