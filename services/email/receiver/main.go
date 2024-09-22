package receiver

import (
	"log"

	"github.com/emersion/go-imap/v2"
)

func Main() error {
	r, err := NewReceiver()
	if err != nil {
		return err
	}
	defer r.Close()

	c := r.imap // XXX
	for _, mailbox := range r.Inboxes /*XXX readinglists! */ {
		mbox, err := c.Select(mailbox, nil).Wait()
		if err != nil {
			return err
		}

		log.Printf("%s contains %d messages\n", mailbox, mbox.NumMessages)

		if mbox.NumMessages < 1 {
			continue
		}

		start := uint32(1)
		const FetchMessages = 10
		stop := start + FetchMessages
		if stop > mbox.NumMessages {
			stop = mbox.NumMessages
		}

		indexes := imap.SeqSet{}
		indexes.AddRange(start, stop)

		/*msgs :=
				for i := 1; i <=
					seqSet := imap.SeqSetNum(i)
					continue
				}

			fetchOptions := &imap.FetchOptions{Envelope: true}
			messages, err := c.Fetch(seqSet, fetchOptions).Collect()
			if err != nil {
				log.Fatalf("failed to fetch first message in INBOX: %v", err)
			}
			log.Printf("subject of first message in INBOX: %v", messages[0].Envelope.Subject)
		}
		*/
	}

	return nil
}
