package monitor

import (
	"errors"
	"time"

	bolt "go.etcd.io/bbolt"
)

var (
	ConditionsBucket  = []byte("Conditions")
	ReportTimesBucket = []byte("ReportTimes")
)

var ErrNilBucket = errors.New("nil bucket")

// ensureBuckets creates the top-level buckets in the database.
func ensureBuckets(tx *bolt.Tx) error {
	for _, bn := range [][]byte{ConditionsBucket, ReportTimesBucket} {
		if _, err := tx.CreateBucketIfNotExists(bn); err != nil {
			return err
		}
	}
	return nil
}

// processReport updates the database with the contents of a report.
//
// Note the clunky interface:
// 1) oldtime will be updated if the condition didn't change.
// 2) oldtime will be ZEROED if the condition changed.
func processReport(
	tx *bolt.Tx,
	serviceName, newcond string,
	newtime time.Time,
	oldtime *time.Time,
) error {
	condkey := []byte(serviceName)
	timekey := []byte(serviceName + ":" + newcond)

	condbucket := tx.Bucket(ConditionsBucket)
	if condbucket == nil {
		return ErrNilBucket
	}
	timebucket := tx.Bucket(ReportTimesBucket)
	if timebucket == nil {
		return ErrNilBucket
	}

	newtimeval, err := newtime.MarshalBinary()
	if err != nil {
		return err
	}

	var oldcond string
	if v := condbucket.Get(condkey); v != nil {
		oldcond = string(v)
	}
	if err := condbucket.Put(condkey, []byte(newcond)); err != nil {
		return err
	}

	var lastInCond time.Time
	if newcond == oldcond {
		// We only care about the old time if the condition didn't change.
		if v := timebucket.Get(timekey); v != nil {
			if err := lastInCond.UnmarshalBinary(v); err != nil {
				return err
			}
		}
	}
	if err := timebucket.Put(timekey, newtimeval); err != nil {
		return err
	}

	*oldtime = lastInCond
	return nil
}
